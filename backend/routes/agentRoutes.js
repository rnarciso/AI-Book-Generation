const express = require('express');
const router = express.Router();
const Story = require('../models/Story');
const LLM_Service = require('../services/LLM_Service');

// --- Helper function to get the story blueprint ---
const getStoryBlueprint = async (storyId) => {
  if (!storyId) {
    throw { status: 400, message: 'Story ID is required' };
  }
  const story = await Story.findById(storyId);
  if (!story) {
    throw { status: 404, message: 'Story not found' };
  }
  return story;
};

// @route   POST /api/agents/architect
// @desc    Run the Architect Agent to generate a plot graph
router.post('/architect', async (req, res) => {
  const { premise, structure } = req.body;
  if (!premise || !structure) {
    return res.status(400).json({ msg: 'Premise and structure are required' });
  }

  const prompt = `
    Based on the following premise and narrative structure, generate a detailed plot graph as a JSON object.
    Premise: "${premise}"
    Narrative Structure: "${structure}"
    The JSON output should contain a list of "event nodes", each with an "id", "title", "description", and "expectedWordCount".
    Respond only with the JSON object.
  `;

  try {
    const plotGraph = await LLM_Service.generate(prompt, 'gpt-4-turbo', true);
    res.json(plotGraph);
  } catch (error) {
    res.status(error.status || 500).json({ msg: error.message || 'Server Error' });
  }
});

// @route   POST /api/agents/worldbuilder
// @desc    Run the World-builder Agent to detail a concept
router.post('/worldbuilder', async (req, res) => {
  const { concept, storyId } = req.body;
  if (!concept || !storyId) {
    return res.status(400).json({ msg: 'Concept and storyId are required' });
  }

  try {
    const story = await getStoryBlueprint(storyId);
    const prompt = `
      Given the existing story world bible: ${JSON.stringify(story.worldBible)},
      Flesh out the following new concept in detail: "${concept}".
      Provide the output as a structured JSON object suitable for inclusion in the world bible.
      Respond only with the JSON object.
    `;
    const worldElement = await LLM_Service.generate(prompt, 'gpt-4-turbo', true);
    res.json(worldElement);
  } catch (error) {
    res.status(error.status || 500).json({ msg: error.message || 'Server Error' });
  }
});

// @route   POST /api/agents/scenewriter
// @desc    Run the Scene Writer Agent
router.post('/scenewriter', async (req, res) => {
  const { eventNodeId, storyId, wordCount } = req.body;
  if (!eventNodeId || !storyId || !wordCount) {
    return res.status(400).json({ msg: 'eventNodeId, storyId, and wordCount are required' });
  }

  try {
    const story = await getStoryBlueprint(storyId);
    const eventNode = story.plotGraph.find(node => node.id === eventNodeId);
    if (!eventNode) {
      return res.status(404).json({ msg: 'Event node not found' });
    }

    const contextPackage = {
      event: eventNode,
      styleGuide: story.styleGuide,
      relevantCharacters: story.characterCodex // In a real app, you might filter this
    };

    const prompt = `
      Write a prose scene based on the following context package.
      The scene should be approximately ${wordCount} words long.
      Context: ${JSON.stringify(contextPackage)}
      Respond only with the narrative prose for the scene.
    `;
    const sceneText = await LLM_Service.generate(prompt);
    res.json({ sceneText });
  } catch (error) {
    res.status(error.status || 500).json({ msg: error.message || 'Server Error' });
  }
});

// @route   POST /api/agents/stylist/analyze
// @desc    Run the Stylist Agent (Analyze Mode)
router.post('/stylist/analyze', async (req, res) => {
  const { sampleText } = req.body;
  if (!sampleText) {
    return res.status(400).json({ msg: 'sampleText is required' });
  }

  const prompt = `
    Analyze the following text sample and generate a "styleGuide" as a JSON object.
    The styleGuide should include keys for "tone", "pacing", "pointOfView", "vocabularyLevel", "stylisticTropes", and "proseRules".
    Sample Text: "${sampleText}"
    Respond only with the JSON object.
  `;
  try {
    const styleGuide = await LLM_Service.generate(prompt, 'gpt-4-turbo', true);
    res.json(styleGuide);
  } catch (error) {
    res.status(error.status || 500).json({ msg: error.message || 'Server Error' });
  }
});

// @route   POST /api/agents/stylist/execute
// @desc    Run the Stylist Agent (Execute Mode)
router.post('/stylist/execute', async (req, res) => {
  const { sceneDraft, storyId } = req.body;
  if (!sceneDraft || !storyId) {
    return res.status(400).json({ msg: 'sceneDraft and storyId are required' });
  }

  try {
    const story = await getStoryBlueprint(storyId);
    const prompt = `
      Rewrite the following scene draft to strictly adhere to the provided style guide.
      Also provide a brief list of changes you made in "revisionNotes".
      Style Guide: ${JSON.stringify(story.styleGuide)}
      Scene Draft: "${sceneDraft}"
      Respond with a JSON object with two keys: "rewrittenText" and "revisionNotes".
    `;
    const result = await LLM_Service.generate(prompt, 'gpt-4-turbo', true);
    res.json(result);
  } catch (error) {
    res.status(error.status || 500).json({ msg: error.message || 'Server Error' });
  }
});

// @route   POST /api/agents/critic/audit
// @desc    Run the Critic Agent (Audit Mode)
router.post('/critic/audit', async (req, res) => {
  const { sceneText, storyId } = req.body;
  if (!sceneText || !storyId) {
    return res.status(400).json({ msg: 'sceneText and storyId are required' });
  }

  try {
    const story = await getStoryBlueprint(storyId);
    const prompt = `
      Act as a literary critic. Audit the following scene for issues related to plot continuity, character consistency, and style guide adherence.
      Use a Chain-of-Thought process:
      1. Thought: Briefly state your goal.
      2. Analysis: Analyze the scene against the story blueprint (plot, characters, style).
      3. Conclusion: State if the scene "pass" or "fail". If it fails, list the specific issues found.
      Story Blueprint for context: ${JSON.stringify(story)}
      Scene Text to Audit: "${sceneText}"
      Respond with a JSON object with two keys: "status" ('pass' or 'fail') and "issues" (an array of strings).
    `;
    const result = await LLM_Service.generate(prompt, 'gpt-4-turbo', true);
    res.json(result);
  } catch (error) {
    res.status(error.status || 500).json({ msg: error.message || 'Server Error' });
  }
});

module.exports = router;
