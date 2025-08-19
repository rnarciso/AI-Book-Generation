import React, { useState } from 'react';
import styled from 'styled-components';
import axios from 'axios';

// Reusing styled-components from ArchitectView for consistency
const ViewContainer = styled.div`
  padding: 20px;
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 15px;
  max-width: 600px;
  margin-bottom: 30px;
`;

const Textarea = styled.textarea`
  padding: 10px;
  border-radius: 4px;
  border: 1px solid #ccc;
  font-family: inherit;
  min-height: 200px; /* Taller for sample text */
`;

const Button = styled.button`
  padding: 12px 20px;
  border-radius: 4px;
  border: none;
  background-color: #2c3e50;
  color: white;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.2s;

  &:hover {
    background-color: #34495e;
  }

  &:disabled {
    background-color: #95a5a6;
    cursor: not-allowed;
  }
`;

const ResultsContainer = styled.div`
  margin-top: 20px;
  background-color: #ecf0f1;
  padding: 20px;
  border-radius: 4px;
`;

const StylistAnalysisView = () => {
  const [sampleText, setSampleText] = useState('');
  const [styleGuide, setStyleGuide] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setStyleGuide(null);

    try {
      const response = await axios.post('http://localhost:5001/api/agents/stylist/analyze', {
        sampleText,
      });
      setStyleGuide(response.data);
    } catch (err) {
      setError(err.response?.data?.msg || 'An error occurred while analyzing the style.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ViewContainer>
      <h1>Stylist Agent (Analysis Mode)</h1>
      <p>Paste a sample of your writing (at least 200 words) to generate a Style Guide.</p>

      <Form onSubmit={handleSubmit}>
        <Textarea
          value={sampleText}
          onChange={(e) => setSampleText(e.target.value)}
          placeholder="Paste your sample text here..."
          required
        />
        <Button type="submit" disabled={isLoading}>
          {isLoading ? 'Analyzing...' : 'Analyze Style'}
        </Button>
      </Form>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {styleGuide && (
        <ResultsContainer>
          <h2>Generated Style Guide</h2>
          {/* TODO: Add a button here to set this as the project's official style guide */}
          <pre>{JSON.stringify(styleGuide, null, 2)}</pre>
        </ResultsContainer>
      )}
    </ViewContainer>
  );
};

export default StylistAnalysisView;
