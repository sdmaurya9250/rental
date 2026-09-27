import { createBrowserRouter } from 'react-router-dom';
import { createElement } from 'react';

import Home from './pages/Home';
import Browse from './pages/Browse';
import MainContent from './pages/MainContent';

const router = createBrowserRouter([
  {
    path: '/',
    element: createElement(Home),
  },
  {
    path: '/browse',
    element: createElement(Browse),
    children: [
      { index: true, element: createElement(MainContent) },
      { path: ':category', element: createElement(MainContent) },
    ],
  },
]);

export default router;