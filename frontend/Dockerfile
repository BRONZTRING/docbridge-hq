# 【第一阶段】：组装阶段。借用 Node 机器人的力量，把 Vue3 代码编译成静态文件
FROM node:20-alpine as build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# 【第二阶段】：实战阶段。选用极其轻量、抗并发极强的 Nginx 战术伺服器
FROM nginx:stable-alpine as production-stage
# 把第一阶段编译好的 dist 文件夹（纯静态网页），放入 Nginx 的展示区
COPY --from=build-stage /app/dist /usr/share/nginx/html
# 暴露 80 端口供外部访问
EXPOSE 80
# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]