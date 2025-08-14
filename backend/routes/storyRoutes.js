const express = require('express');
const router = express.Router();
const Story = require('../models/Story');

// @route   POST /api/stories
// @desc    Create a new Story Blueprint from a blank template
// @access  Public
router.post('/', async (req, res) => {
  try {
    // Create a new story instance with default values from the schema
    const newStory = new Story({});
    await newStory.save();
    res.status(201).json(newStory);
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server Error');
  }
});

// @route   GET /api/stories/:id
// @desc    Get a Story Blueprint by ID
// @access  Public
router.get('/:id', async (req, res) => {
  try {
    const story = await Story.findById(req.params.id);
    if (!story) {
      return res.status(404).json({ msg: 'Story not found' });
    }
    res.json(story);
  } catch (err) {
    console.error(err.message);
    if (err.kind === 'ObjectId') {
      return res.status(404).json({ msg: 'Story not found' });
    }
    res.status(500).send('Server Error');
  }
});

// @route   PUT /api/stories/:id
// @desc    Update a Story Blueprint with a full JSON object
// @access  Public
router.put('/:id', async (req, res) => {
  try {
    let story = await Story.findById(req.params.id);
    if (!story) {
      return res.status(404).json({ msg: 'Story not found' });
    }

    // The request body should contain the entire updated Story Blueprint object
    const updatedBlueprint = req.body;

    // Update all fields based on the request body
    story.set(updatedBlueprint);

    // Mongoose's `set` will automatically handle nested objects and timestamps
    await story.save();

    res.json(story);
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server Error');
  }
});

module.exports = router;
