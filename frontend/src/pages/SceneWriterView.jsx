import React, { useState, useEffect, useCallback } from 'react';
import styled from 'styled-components';
import axios from 'axios';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css'; // import styles

const ViewContainer = styled.div`
  padding: 20px;
`;

const Form = styled.form`
  display: flex;
  align-items: flex-end;
  gap: 15px;
  max-width: 800px;
  margin-bottom: 30px;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  flex-grow: 1;
`;

const Select = styled.select`
  padding: 10px;
  border-radius: 4px;
  border: 1px solid #ccc;
`;

const Input = styled.input`
  padding: 10px;
  border-radius: 4px;
  border: 1px solid #ccc;
`;

const Button = styled.button`
  padding: 10px 20px;
  height: 40px;
  border-radius: 4px;
  border: none;
  background-color: #2c3e50;
  color: white;
  font-size: 16px;
  cursor: pointer;
  &:disabled { background-color: #95a5a6; }
`;

const EditorContainer = styled.div`
  margin-top: 20px;
`;

const ActionsContainer = styled.div`
  margin-top: 10px;
  display: flex;
  gap: 10px;
`;

const ResultPopup = styled.div`
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80%;
  max-width: 800px;
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.3);
  z-index: 1000;
`;

const SceneWriterView = () => {
  const [story, setStory] = useState(null);
  const [storyId, setStoryId] = useState(localStorage.getItem('currentStoryId'));
  const [selectedNodeId, setSelectedNodeId] = useState('');
  const [wordCount, setWordCount] = useState(500);
  const [sceneText, setSceneText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [stylistResult, setStylistResult] = useState(null);
  const [criticResult, setCriticResult] = useState(null);

  useEffect(() => {
    if (storyId) {
      axios.get(`http://localhost:5001/api/stories/${storyId}`)
        .then(res => setStory(res.data))
        .catch(() => setError('Could not fetch story.'));
    } else {
      setError('No story loaded. Create one in the Blueprint Editor.');
    }
  }, [storyId]);

  const handleWriteScene = async (e) => {
    e.preventDefault();
    if (!selectedNodeId) {
      alert('Please select an event node.');
      return;
    }
    setIsLoading(true);
    setError('');
    try {
      const res = await axios.post('http://localhost:5001/api/agents/scenewriter', {
        eventNodeId: selectedNodeId,
        storyId,
        wordCount
      });
      setSceneText(res.data.sceneText);
    } catch (err) {
      setError(err.response?.data?.msg || 'Failed to write scene.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStylist = async () => {
      setIsLoading(true);
      try {
          const res = await axios.post('http://localhost:5001/api/agents/stylist/execute', { sceneDraft: sceneText, storyId });
          setStylistResult(res.data);
      } catch (err) { setError('Stylist agent failed.'); }
      setIsLoading(false);
  };

  const handleCritic = async () => {
      setIsLoading(true);
      try {
          const res = await axios.post('http://localhost:5001/api/agents/critic/audit', { sceneText, storyId });
          setCriticResult(res.data);
      } catch (err) { setError('Critic agent failed.'); }
      setIsLoading(false);
  };

  return (
    <ViewContainer>
      <h1>Scene Writer</h1>
      <p>Select a plot event and generate the prose for the scene.</p>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      <Form onSubmit={handleWriteScene}>
        <FormGroup>
          <label>Event Node</label>
          <Select value={selectedNodeId} onChange={e => setSelectedNodeId(e.target.value)} required>
            <option value="">Select an event...</option>
            {story?.plotGraph?.map(node => (
              <option key={node.id} value={node.id}>{node.title}</option>
            ))}
          </Select>
        </FormGroup>
        <FormGroup>
          <label>Word Count</label>
          <Input type="number" value={wordCount} onChange={e => setWordCount(e.target.value)} />
        </FormGroup>
        <Button type="submit" disabled={isLoading}>{isLoading ? 'Writing...' : 'Write Scene'}</Button>
      </Form>

      <EditorContainer>
        <ReactQuill theme="snow" value={sceneText} onChange={setSceneText} />
      </EditorContainer>

      {sceneText && (
        <ActionsContainer>
          <Button onClick={handleStylist} disabled={isLoading}>Refine with Stylist</Button>
          <Button onClick={handleCritic} disabled={isLoading}>Audit with Critic</Button>
        </ActionsContainer>
      )}

      {stylistResult && (
        <ResultPopup>
          <h2>Stylist Result</h2>
          <h4>Rewritten Text:</h4>
          <p>{stylistResult.rewrittenText}</p>
          <h4>Revision Notes:</h4>
          <ul>{stylistResult.revisionNotes.map((note, i) => <li key={i}>{note}</li>)}</ul>
          <Button onClick={() => setStylistResult(null)}>Close</Button>
        </ResultPopup>
      )}

      {criticResult && (
        <ResultPopup>
          <h2>Critic Result</h2>
          <p>Status: <strong style={{color: criticResult.status === 'pass' ? 'green' : 'red'}}>{criticResult.status}</strong></p>
          {criticResult.issues?.length > 0 && (
            <>
              <h4>Issues Found:</h4>
              <ul>{criticResult.issues.map((issue, i) => <li key={i}>{issue}</li>)}</ul>
            </>
          )}
          <Button onClick={() => setCriticResult(null)}>Close</Button>
        </ResultPopup>
      )}

    </ViewContainer>
  );
};

export default SceneWriterView;
