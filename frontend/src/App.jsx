import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import styled from 'styled-components';

import ArchitectView from './pages/ArchitectView';
import StylistAnalysisView from './pages/StylistAnalysisView';
import StoryBlueprintEditor from './pages/StoryBlueprintEditor';
import WorldBuilderView from './pages/WorldBuilderView';
import SceneWriterView from './pages/SceneWriterView';

// Placeholder pages (we will create these files next)
const Home = () => <h1>Welcome to AuthorAI</h1>;


const AppContainer = styled.div`
  display: flex;
  height: 100vh;
`;

const Sidebar = styled.nav`
  width: 220px;
  background: #2c3e50;
  padding: 20px;
  color: white;

  a {
    display: block;
    color: white;
    text-decoration: none;
    padding: 10px 15px;
    border-radius: 4px;
    margin-bottom: 10px;
    transition: background-color 0.2s;

    &:hover {
      background-color: #34495e;
    }
  }
`;

const MainContent = styled.main`
  flex-grow: 1;
  padding: 30px;
  overflow-y: auto;
`;


function App() {
  return (
    <Router>
      <AppContainer>
        <Sidebar>
          <h2>AuthorAI</h2>
          <Link to="/">Home</Link>
          <Link to="/architect">Architect</Link>
          <Link to="/worldbuilder">World-Builder</Link>
          <Link to="/scenewriter">Scene Writer</Link>
          <Link to="/stylist">Stylist</Link>
          <Link to="/blueprint">Blueprint Editor</Link>
        </Sidebar>
        <MainContent>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/architect" element={<ArchitectView />} />
            <Route path="/worldbuilder" element={<WorldBuilderView />} />
            <Route path="/scenewriter" element={<SceneWriterView />} />
            <Route path="/stylist" element={<StylistAnalysisView />} />
            <Route path="/blueprint" element={<StoryBlueprintEditor />} />
          </Routes>
        </MainContent>
      </AppContainer>
    </Router>
  );
}

export default App;
