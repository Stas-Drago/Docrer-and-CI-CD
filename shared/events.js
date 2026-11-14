import amqp from 'amqplib';

const exchange = 'mathcourses.events';

export async function createEventBus(serviceName) {
  const url = process.env.RABBITMQ_URL || 'amqp://rabbitmq';
  const connection = await amqp.connect(url);
  const channel = await connection.createChannel();
  await channel.assertExchange(exchange, 'topic', { durable: true });
  return {
    async publish(eventType, payload, correlationId = crypto.randomUUID()) {
      const event = { eventId: crypto.randomUUID(), eventType, occurredAt: new Date().toISOString(), schemaVersion: 1, correlationId, payload };
      channel.publish(exchange, eventType, Buffer.from(JSON.stringify(event)), { persistent: true, contentType: 'application/json', correlationId });
      console.log(`${serviceName}: published ${eventType}`);
      return event;
    },
    async subscribe(eventTypes, handler) {
      const { queue } = await channel.assertQueue('', { exclusive: true, autoDelete: true });
      for (const eventType of eventTypes) await channel.bindQueue(queue, exchange, eventType);
      await channel.consume(queue, async (message) => {
        if (!message) return;
        try { await handler(JSON.parse(message.content.toString())); channel.ack(message); }
        catch (error) { console.error(`${serviceName}: event failed`, error); channel.nack(message, false, false); }
      });
    },
    close: () => connection.close()
  };
}
