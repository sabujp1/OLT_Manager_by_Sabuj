FROM node:18-alpine

WORKDIR /app

# Copy package configuration and install dependencies
COPY package.json ./
RUN npm install

# Copy application source
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
