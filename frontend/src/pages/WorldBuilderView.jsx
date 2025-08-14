import React, { useState, useEffect, useCallback } from 'react';
import styled from 'styled-components';
import axios from 'axios';
import ReactJson from 'react-json-view';

const ViewContainer = styled.div`
  padding: 20px;
  display: flex;
  gap: 30px;
`;

const MainPanel = styled.div`
  flex: 2;
`;

const SidePanel = styled.div`
  flex: 1;
  background-color: #f8f9fa;
  padding: 20px;
  border-radius: 6px;
`;

const TabContainer = styled.div`
  display: flex;
  border-bottom: 1px solid #ccc;
  margin-bottom: 20px;
`;

const TabButton = styled.button`
  padding: 10px 20px;
  border: 1px solid transparent;
  border-bottom: none;
  cursor: pointer;
  background-color: ${props => props.active ? '#fff' : 'transparent'};
  border-color: ${props => props.active ? '#ccc' : 'transparent'};
  border-radius: 4px 4px 0 0;
  margin-bottom: -1px;
`;

const Textarea = styled.textarea`
  width: 100%;
  min-height: 100px;
  padding: 10px;
  border-radius: 4px;
  border: 1px solid #ccc;
  margin-bottom: 10px;
`;

const Button = styled.button`
  width: 100%;
  padding: 12px 20px;
  border-radius: 4px;
  border: none;
  background-color: #2c3e50;
  color: white;
  font-size: 16px;
  cursor: pointer;
  &:disabled { background-color: #95a5a6; }
`;

const WorldBuilderView = () => {
  const [story, setStory] = useState(null);
  const [storyId, setStoryId] = useState(localStorage.getItem('currentStoryId'));
  const [activeTab, setActiveTab] = useState('characterCodex');
  const [concept, setConcept] = useState('');
  const [generatedElement, setGeneratedElement] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchStory = useCallback(async () => {
    if (!storyId) {
      setError('No story loaded. Please create a new story in the Blueprint Editor first.');
      return;
    }
    setIsLoading(true);
    try {
      const response = await axios.get(`http://localhost:5001/api/stories/${storyId}`);
      setStory(response.data);
    } catch (err) {
      setError('Could not fetch the story.');
    } finally {
      setIsLoading(false);
    }
  }, [storyId]);

  useEffect(() => {
    fetchStory();
  }, [fetchStory]);

  const handleGenerate = async () => {
    if (!concept) return;
    setIsLoading(true);
    setError('');
    setGeneratedElement(null);
    try {
      const response = await axios.post('http://localhost:5001/api/agents/worldbuilder', {
        concept,
        storyId,
      });
      setGeneratedElement(response.data);
    } catch (err) {
      setError(err.response?.data?.msg || 'Failed to generate world element.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleMerge = async () => {
      // This is a simplified merge logic. A real app would need a more robust way
      // to handle different structures (arrays vs objects) and keys.
      if (!generatedElement) return;

      const newStory = { ...story };
      const key = Object.keys(generatedElement)[0]; // e.g., "newCharacter"
      const value = generatedElement[key];

      // Assuming the key from the LLM tells us where to put the data
      if (activeTab === 'characterCodex') {
          newStory.characterCodex[key] = value;
      } else if (activeTab === 'locations') {
          newStory.worldBible.locations[key] = value;
      } // etc.

      try {
          const response = await axios.put(`http://localhost:5001/api/stories/${storyId}`, newStory);
          setStory(response.data);
          setGeneratedElement(null); // Clear after merging
          setConcept('');
          alert('Element merged into Story Blueprint!');
      } catch(err) {
          setError('Failed to save the updated story.');
      }
  };

  const renderActiveTabData = () => {
    if (!story) return null;
    if (activeTab === 'locations') return story.worldBible.locations;
    if (activeTab === 'magicSystems') return story.worldBible.magicSystems;
    return story[activeTab];
  };

  return (
    <ViewContainer>
      <MainPanel>
        <h1>World-Builder</h1>
        <TabContainer>
          <TabButton active={activeTab === 'characterCodex'} onClick={() => setActiveTab('characterCodex')}>Characters</TabButton>
          <TabButton active={activeTab === 'locations'} onClick={() => setActiveTab('locations')}>Locations</TabButton>
          <TabButton active={activeTab === 'magicSystems'} onClick={() => setActiveTab('magicSystems')}>Magic Systems</TabButton>
        </TabContainer>
        {isLoading && !story && <p>Loading Story Blueprint...</p>}
        {error && <p style={{color: 'red'}}>{error}</p>}
        {story && (
          <ReactJson
            src={renderActiveTabData()}
            name={activeTab}
            theme="rjv-default"
            collapsed={1}
          />
        )}
      </MainPanel>
      <SidePanel>
        <h2>Generate New Element</h2>
        <p>Describe a new concept for the active category (e.g., "a grumpy dwarf blacksmith" for Characters).</p>
        <Textarea
          value={concept}
          onChange={(e) => setConcept(e.target.value)}
          placeholder="Describe your new concept..."
        />
        <Button onClick={handleGenerate} disabled={isLoading || !concept}>
          {isLoading ? 'Generating...' : 'Generate Details'}
        </Button>

        {generatedElement && (
          <div style={{marginTop: '20px'}}>
            <h3>Generated Element</h3>
            <ReactJson src={generatedElement} name="newElement" collapsed={1} />
            <Button onClick={handleMerge} style={{marginTop: '10px'}}>Merge into Blueprint</Button>
          </div>
        )}
      </SidePanel>
    </ViewContainer>
  );
};

export default WorldBuilderView;
