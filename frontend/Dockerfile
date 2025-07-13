# Multi-stage Dockerfile for Pathavana Frontend
# Optimized for production with security scanning and minimal bundle size

# Base stage with Node.js
FROM node:18-alpine as base

# Set environment variables
ENV NODE_ENV=production
ENV NPM_CONFIG_LOGLEVEL=warn
ENV NPM_CONFIG_COLOR=false

# Install security updates
RUN apk update && apk upgrade && apk add --no-cache curl

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Dependencies stage
FROM base as dependencies

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Development dependencies stage
FROM dependencies as dev-dependencies

# Install all dependencies (including dev)
RUN npm ci

# Development stage
FROM dev-dependencies as development

WORKDIR /app

# Copy source code
COPY . .

# Change ownership to non-root user
RUN chown -R nextjs:nodejs /app

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Start development server
CMD ["npm", "start"]

# Build stage
FROM dev-dependencies as builder

WORKDIR /app

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Security scanning stage
FROM builder as security-scan

# Install security scanning tools
RUN npm install -g npm-audit-ci retire

# Run security scans
RUN npm audit --audit-level=moderate || true
RUN retire --js --outputformat=json || true

# Production stage
FROM base as production

WORKDIR /app

# Copy production dependencies
COPY --from=dependencies /app/node_modules ./node_modules

# Copy built application
COPY --from=builder /app/build ./build

# Copy necessary files
COPY package*.json ./
COPY public ./public

# Install serve for production
RUN npm install -g serve@14.2.0

# Create necessary directories and set permissions
RUN mkdir -p /app/logs && \
    chown -R nextjs:nodejs /app

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Serve the built application
CMD ["serve", "-s", "build", "-l", "3000"]

# Nginx production stage (alternative serving method)
FROM nginx:alpine as nginx-production

# Install security updates
RUN apk update && apk upgrade

# Copy built application
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create non-root user
RUN addgroup -g 1001 -S nginx && \
    adduser -S nginx -u 1001 -G nginx

# Set permissions
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d

# Create pid directory
RUN mkdir -p /var/run/nginx && \
    chown -R nginx:nginx /var/run/nginx

# Switch to non-root user
USER nginx

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]