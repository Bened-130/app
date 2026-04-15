import * as FaceDetector from 'expo-face-detector';

// 128-dimensional face descriptor (simplified - use face-api.js in production)
export interface FaceDescriptor {
  raw: number[];
}

const SIMILARITY_THRESHOLD = 0.6;

// Calculate Euclidean distance between two face descriptors
export function euclideanDistance(desc1: number[], desc2: number[]): number {
  if (desc1.length !== desc2.length) return Infinity;
  
  let sum = 0;
  for (let i = 0; i < desc1.length; i++) {
    const diff = desc1[i] - desc2[i];
    sum += diff * diff;
  }
  return Math.sqrt(sum);
}

// Normalize face descriptor
export function normalizeDescriptor(descriptor: number[]): number[] {
  const magnitude = Math.sqrt(descriptor.reduce((sum, val) => sum + val * val, 0));
  return descriptor.map(val => val / magnitude);
}

// Compare face with database
export function findBestMatch(
  detectedFace: number[],
  databaseFaces: { studentId: string; descriptor: number[]; name: string }[]
): { match: boolean; studentId?: string; name?: string; confidence: number } {
  let bestMatch = { studentId: '', name: '', distance: Infinity };
  
  for (const record of databaseFaces) {
    const distance = euclideanDistance(detectedFace, record.descriptor);
    if (distance < bestMatch.distance) {
      bestMatch = { ...record, distance };
    }
  }
  
  const confidence = 1 - (bestMatch.distance / 2); // Normalize to 0-1
  
  return {
    match: bestMatch.distance < SIMILARITY_THRESHOLD,
    studentId: bestMatch.studentId,
    name: bestMatch.name,
    confidence,
  };
}

// Extract face features from detected face
// Note: In production, use TensorFlow.js face-api.js for accurate embeddings
export async function extractFaceFeatures(face: FaceDetector.FaceFeature): Promise<number[]> {
  // Placeholder: Generate 128D vector from face landmarks
  // In production, this uses a deep neural network
  const landmarks = [
    face.bounds.origin.x,
    face.bounds.origin.y,
    face.bounds.size.width,
    face.bounds.size.height,
    ...(face.leftEyePosition ? [face.leftEyePosition.x, face.leftEyePosition.y] : [0, 0]),
    ...(face.rightEyePosition ? [face.rightEyePosition.x, face.rightEyePosition.y] : [0, 0]),
    ...(face.noseBasePosition ? [face.noseBasePosition.x, face.noseBasePosition.y] : [0, 0]),
  ];
  
  // Pad to 128 dimensions with derived values
  const descriptor: number[] = [];
  for (let i = 0; i < 128; i++) {
    const baseIdx = i % landmarks.length;
    descriptor.push(landmarks[baseIdx] * (1 + i * 0.01) + Math.random() * 0.001);
  }
  
  return normalizeDescriptor(descriptor);
}