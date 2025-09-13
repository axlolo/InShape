// Available shapes for daily challenges
export const availableShapes = [
  {
    name: "Circle",
    image: "/shapes/circle-1.svg",
    description: "Run a circular route today!"
  },
  {
    name: "Rectangle",
    image: "/shapes/rectangle-1.svg",
    description: "Create a perfect rectangular running path!"
  },
  {
    name: "Triangle",
    image: "/shapes/triangle-1.svg",
    description: "Challenge yourself with a triangular route!"
  },
  {
    name: "Star",
    image: "/shapes/star-1.svg",
    description: "Shine bright with a star-shaped run!"
  },
  {
    name: "Diamond",
    image: "/shapes/diamond-1.svg",
    description: "Run a diamond pattern route!"
  },
  {
    name: "Heart",
    image: "/shapes/heart-1.svg",
    description: "Show some love with a heart-shaped route!"
  },
  {
    name: "Hexagon",
    image: "/shapes/hexagon-1.svg",
    description: "Six-sided challenge awaits!"
  },
  {
    name: "Perfect Square",
    image: "/shapes/perfect-square.svg",
    description: "Master the perfect square route!"
  },
  {
    name: "Figure Eight",
    image: "/shapes/figure-eight-1.svg",
    description: "Infinity and beyond with a figure-8 route!"
  }
];

// Get today's shape (for now, always rectangle for the challenge)
export const getTodaysShape = () => {
  // For the challenge feature, we're focusing on rectangles
  return availableShapes.find(shape => shape.name === "Rectangle") || availableShapes[1];
};

export default availableShapes;
