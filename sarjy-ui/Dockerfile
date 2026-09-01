# Build with Vite, serve the static output with nginx, and proxy /api to the
# backend container — so the browser sees one origin and there is no CORS.
FROM node:22-alpine AS build
WORKDIR /ui

COPY package.json package-lock.json ./
RUN npm ci

COPY . ./
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /ui/dist /usr/share/nginx/html

EXPOSE 80
