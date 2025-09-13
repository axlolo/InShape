// Available shapes for daily challenges
export const availableShapes = [
  {
    name: "Rectangle",
    id: "rectangle", 
    image: "/shapes/rectangle-1.svg",
    description: "Create a perfect rectangular running path!"
  },
  {
    name: "Circle", 
    id: "oval",
    image: "/shapes/circle-1.svg",
    description: "Run a perfect circular route today!"
  },
  {
    name: "Plus",
    id: "plus",
    image: "/shapes/plus-1.svg", 
    description: "Cross paths with a plus-shaped route!"
  },
  {
    name: "Circle",
    id: "circle",
    image: "/shapes/circle-1.svg",
    description: "Run a circular route today!"
  },
  {
    name: "Triangle",
    id: "triangle",
    image: "/shapes/triangle-1.svg",
    description: "Challenge yourself with a triangular route!"
  },
  {
    name: "Star",
    id: "star",
    image: "/shapes/star-1.svg",
    description: "Shine bright with a star-shaped run!"
  },
  {
    name: "Diamond",
    id: "diamond",
    image: "/shapes/diamond-1.svg",
    description: "Run a diamond pattern route!"
  },
  {
    name: "Heart",
    id: "heart",
    image: "/shapes/heart-1.svg",
    description: "Show some love with a heart-shaped route!"
  },
  {
    name: "Hexagon",
    id: "hexagon",
    image: "/shapes/hexagon-1.svg",
    description: "Six-sided challenge awaits!"
  },
  {
    name: "Perfect Square",
    id: "square",
    image: "/shapes/perfect-square.svg",
    description: "Master the perfect square route!"
  },
  {
    name: "Figure Eight",
    id: "figure-eight",
    image: "/shapes/figure-eight-1.svg",
    description: "Infinity and beyond with a figure-8 route!"
  }
];

// Primary shapes for the main challenge feature  
export const primaryShapes = availableShapes.slice(0, 3); // Rectangle, Circle, Plus

// Get shape by ID
export const getShapeById = (id: string) => {
  return availableShapes.find(shape => shape.id === id) || availableShapes[0];
};

// Get today's shape (dynamic based on selection)
export const getTodaysShape = (selectedShapeId?: string) => {
  if (selectedShapeId) {
    return getShapeById(selectedShapeId);
  }
  // Default to rectangle
  return availableShapes[0];
};

export default availableShapes;
