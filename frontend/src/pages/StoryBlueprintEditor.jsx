import React, { useState, useEffect, useCallback } from 'react';
import styled from 'styled-components';
import axios from 'axios';
import ReactJson from 'react-json-view';

const ViewContainer = styled.div`
  padding: 20px;
`;

const Button = styled.button`
  padding: 12px 20px;
  margin-right: 10px;
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

const EditorControls = styled.div`
  margin-bottom: 20px;
`;

const StoryBlueprintEditor = () => {
  const [story, setStory] = useState(null);
  const [storyId, setStoryId] = useState(localStorage.getItem('currentStoryId'));
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchStory = useCallback(async (id) => {
    if (!id) return;
    setIsLoading(true);
    setError('');
    try {
      const response = await axios.get(`http://localhost:5001/api/stories/${id}`);
      setStory(response.data);
    } catch (err) {
      setError('Could not fetch story. It might not exist.');
      setStory(null);
      setStoryId(null);
      localStorage.removeItem('currentStoryId');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (storyId) {
      fetchStory(storyId);
    }
  }, [storyId, fetchStory]);

  const createNewStory = async () => {
    setIsLoading(true);
    setError('');
    try {
      const response = await axios.post('http://localhost:5001/api/stories');
      const newStory = response.data;
      setStory(newStory);
      setStoryId(newStory._id);
      localStorage.setItem('currentStoryId', newStory._id);
    } catch (err) {
      setError('Failed to create a new story.');
    } finally {
      setIsLoading(false);
    }
  };

  const saveStory = async () => {
    if (!story) return;
    setIsLoading(true);
    setError('');
    try {
      // The react-json-view component provides the updated src object on edit
      const response = await axios.put(`http://localhost:5001/api/stories/${storyId}`, story);
      setStory(response.data); // Update with the saved version
      alert('Story Blueprint Saved!');
    } catch (err) {
      setError('Failed to save the story.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleJsonEdit = (edit) => {
    setStory(edit.updated_src);
    return true; // Important to allow the edit
  };

  return (
    <ViewContainer>
      <h1>Story Blueprint Editor</h1>
      <p>View and manually edit the master JSON document for your story.</p>

      <EditorControls>
        <Button onClick={createNewStory} disabled={isLoading}>
          Create New Story
        </Button>
        {story && (
          <Button onClick={saveStory} disabled={isLoading}>
            {isLoading ? 'Saving...' : 'Save Blueprint'}
          </Button>
        )}
      </EditorControls>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {isLoading && !story && <p>Loading...</p>}

      {story ? (
        <ReactJson
          src={story}
          theme="monokai"
          name={false}
          displayObjectSize={false}
          displayDataTypes={false}
          onEdit={handleJsonEdit}
          onAdd={handleJsonEdit}
          onDelete={handleJsonEdit}
        />
      ) : (
        !isLoading && <p>No story loaded. Create a new one to begin.</p>
      )}
    </ViewContainer>
  );
};

export default StoryBlueprintEditor;
