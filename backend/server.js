const express = require('express');
const mongoose = require('mongoose');
const dotenv = require('dotenv');
const cors = require('cors');

// Load environment variables
dotenv.config();

// Initialize Express app
const app = express();

// Middlewares
app.use(cors());
app.use(express.json()); // To parse JSON bodies

// --- Database Connection ---
const connectDB = async () => {
  try {
    await mongoose.connect(process.env.MONGO_URI);
    console.log('MongoDB Connected...');
  } catch (err) {
    console.error(err.message);
    // Exit process with failure
    process.exit(1);
  }
};

connectDB();

// --- Basic Route for Testing ---
app.get('/', (req, res) => {
  res.send('AuthorAI API is running...');
});

// --- API Routes ---
app.use('/api/stories', require('./routes/storyRoutes'));
app.use('/api/agents', require('./routes/agentRoutes'));


// --- Start Server ---
const PORT = process.env.PORT || 5001;

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
