const axios = require('axios');

// This service class encapsulates all communication with the external LLM API.
// This makes it easy to swap out the LLM provider (e.g., from OpenAI to Google)
// without changing the agent logic.

class LLM_Service {
  constructor() {
    this.apiKey = process.env.LLM_API_KEY;
    // Using OpenAI's endpoint as a placeholder. This could also be an env variable.
    this.apiUrl = 'https://api.openai.com/v1/chat/completions';

    if (!this.apiKey) {
      throw new Error('LLM_API_KEY is not defined in the environment variables.');
    }

    this.client = axios.create({
      baseURL: this.apiUrl,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`
      }
    });
  }

  /**
   * Sends a prompt to the LLM and returns the response.
   * @param {string} prompt - The complete prompt to send to the model.
   * @param {string} model - The name of the model to use (e.g., 'gpt-4-turbo').
   * @param {boolean} jsonMode - Whether to enable JSON mode for the response.
   * @returns {Promise<string|object>} - The content of the LLM's response.
   */
  async generate(prompt, model = 'gpt-4-turbo', jsonMode = false) {
    console.log(`Sending prompt to LLM (model: ${model})...`);

    const body = {
      model: model,
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.7,
    };

    if (jsonMode) {
      body.response_format = { type: 'json_object' };
    }

    try {
      const response = await this.client.post('', body);

      if (response.data && response.data.choices && response.data.choices.length > 0) {
        const content = response.data.choices[0].message.content;
        console.log('LLM response received successfully.');

        if (jsonMode) {
          // The API guarantees valid JSON in the response string when jsonMode is on.
          return JSON.parse(content);
        }
        return content;
      } else {
        throw new Error('LLM response format is invalid.');
      }
    } catch (error) {
      console.error('Error calling LLM API:', error.response ? error.response.data : error.message);
      // Check for the specific "Unprocessable Entity" case mentioned in the prompt
      if (error.response && error.response.status === 422) {
        throw {
          status: 422,
          message: 'Unprocessable Entity: The LLM API could not process the request. This may be due to missing information in the prompt.',
          originalError: error.response.data
        };
      }
      throw new Error('Failed to get a response from the LLM API.');
    }
  }
}

// Export a singleton instance of the service
module.exports = new LLM_Service();
