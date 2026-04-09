FROM node:20-alpine

WORKDIR /app

ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8001
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}
ENV NEXT_TELEMETRY_DISABLED=1

COPY package.json /app/package.json
RUN npm install

COPY . /app
RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start"]
