FROM node:22-alpine
WORKDIR /app
COPY package.json ./
RUN npm install --omit=dev
COPY shared ./shared
ARG SERVICE
ENV SERVICE=${SERVICE}
COPY services/${SERVICE} ./services/${SERVICE}
EXPOSE 3000
CMD ["sh", "-c", "node services/${SERVICE}/index.js"]
