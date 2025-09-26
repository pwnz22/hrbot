const config = {
  development: {
    API_BASE_URL: 'http://localhost:8080'
  },
  production: {
    // Замените на URL вашего продакшен API
    API_BASE_URL: 'https://your-api-domain.com'
  }
}

const environment = process.env.NODE_ENV || 'development'

export default config[environment]