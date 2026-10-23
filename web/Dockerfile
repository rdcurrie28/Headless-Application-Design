FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.27-alpine
ENV API_UPSTREAM=http://api:8000 API_KEY=""
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY 15-demo-auth.sh /docker-entrypoint.d/15-demo-auth.sh
USER root
RUN chmod 755 /docker-entrypoint.d/15-demo-auth.sh
USER 101
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
