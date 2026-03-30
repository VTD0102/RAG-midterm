FROM node:20-alpine

WORKDIR /app

# Copy package files first to leverage Docker cache
COPY package*.json ./
RUN npm install

# Copy the rest of the application code
COPY . .

# Expose Vite dev port
EXPOSE 5173

# Start Vite dev server bound to all network interfaces
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
