# Frontend Dockerfile (Vite + React)
FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy application files
COPY . .

# Expose Vite dev port or production port
EXPOSE 5173

# Run the dev server (or build for prod: npm run build && npx serve -s dist)
CMD ["npm", "run", "dev", "--", "--host"]
