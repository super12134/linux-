const express = require('express');
const redis = require('redis');

const app = express();
const PORT = process.env.PORT || 3000;
const REDIS_HOST = process.env.REDIS_HOST || 'localhost';

// 连接 Redis
const client = redis.createClient({
  url: `redis://${REDIS_HOST}:6379`
});

client.on('error', (err) => console.error('Redis Client Error', err));

app.get('/', async (req, res) => {
  try {
    // 增加计数值
    const count = await client.incr('visitor_count');
    res.send(`
      <html>
        <head><title>Docker Compose Demo</title></head>
        <body style="font-family: sans-serif; text-align: center; margin-top: 100px;">
          <h1>🚀 Docker Compose 学习</h1>
          <p>第 <strong style="font-size: 2em; color: #e74c3c;">${count}</strong> 次访问</p>
          <p style="color: #888;">Redis 计111数器中...</p>
          <hr style="width: 200px;">
          <p style="font-size: 0.8em; color: #aaa;">
            Node.js ${process.version} | Redis connected
          </p>
        </body>
      </html>
    `);
  } catch (err) {
    res.status(500).send(`Redis error: ${err.message}`);
  }
});

// 连接 Redis 后启动服务
(async () => {
  await client.connect();
  app.listen(PORT, () => {
    console.log(`Server running on http://0.0.0.0:${PORT}`);
  });
})();
