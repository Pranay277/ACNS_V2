# SCIARS frontend — production image (P2-11).
#
# Two-stage build: compile the Vite bundle with Node, then serve the static
# output with Nginx. VITE_API_URL is a build-time argument; use "/api" for the
# same-origin Nginx proxy in docker-compose, or the deployed backend origin.
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
