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

// Get today's shape (can be made dynamic based on date)
export const getTodaysShape = () => {
  // For now, return a random shape. In production, this could be based on date
  // or fetched from an API
  const today = new Date();
  const dayOfYear = Math.floor((today.getTime() - new Date(today.getFullYear(), 0, 0).getTime()) / (1000 * 60 * 60 * 24));
  const shapeIndex = dayOfYear % availableShapes.length;
  return availableShapes[shapeIndex];
};

export default availableShapes;
