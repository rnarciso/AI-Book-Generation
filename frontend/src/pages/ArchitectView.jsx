import React, { useState } from 'react';
import styled from 'styled-components';
import axios from 'axios';

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
  min-height: 100px;
`;

const Select = styled.select`
  padding: 10px;
  border-radius: 4px;
  border: 1px solid #ccc;
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

const ArchitectView = () => {
  const [premise, setPremise] = useState('');
  const [structure, setStructure] = useState('Three-Act Structure');
  const [plotGraph, setPlotGraph] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setPlotGraph(null);

    try {
      const response = await axios.post('http://localhost:5001/api/agents/architect', {
        premise,
        structure,
      });
      setPlotGraph(response.data);
    } catch (err) {
      setError(err.response?.data?.msg || 'An error occurred while generating the plot.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ViewContainer>
      <h1>Architect Agent</h1>
      <p>Generate the foundational plot graph for your story.</p>

      <Form onSubmit={handleSubmit}>
        <Textarea
          value={premise}
          onChange={(e) => setPremise(e.target.value)}
          placeholder="Enter your story premise here... (e.g., A young wizard discovers a conspiracy at his magical school)"
          required
        />
        <Select value={structure} onChange={(e) => setStructure(e.target.value)}>
          <option value="Three-Act Structure">Three-Act Structure</option>
          <option value="The Hero's Journey">The Hero's Journey</option>
          <option value="Fichtean Curve">Fichtean Curve</option>
        </Select>
        <Button type="submit" disabled={isLoading}>
          {isLoading ? 'Generating...' : 'Generate Plot'}
        </Button>
      </Form>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {plotGraph && (
        <ResultsContainer>
          <h2>Generated Plot Graph</h2>
          {/* TODO: Add a button here to merge this into the main blueprint */}
          <pre>{JSON.stringify(plotGraph, null, 2)}</pre>
        </ResultsContainer>
      )}
    </ViewContainer>
  );
};

export default ArchitectView;
