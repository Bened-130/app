import React, { useEffect, useState, useRef } from 'react';
import { 
  View, Text, StyleSheet, Dimensions, ActivityIndicator, Alert 
} from 'react-native';
import { Camera, useCameraDevice, useCameraPermission, useFrameProcessor } from 'react-native-vision-camera';
import { useFaceDetector } from 'react-native-vision-camera-face-detector';
import { Worklets } from 'react-native-worklets-core';
import Animated, { 
  useSharedValue, useAnimatedStyle, withSpring, withRepeat, 
  withTiming, interpolate 
} from 'react-native-reanimated';
import { useNavigation } from '@react-navigation/native';
import { supabase } from '../../lib/supabase';
import { useAuthStore } from '../../store/authStore';
import { findBestMatch, extractFaceFeatures } from '../../utils/faceRecognition';
import GlassmorphismCard from '../../components/GlassmorphismCard';
import { runOnJS } from 'react-native-reanimated';

const { width, height } = Dimensions.get('window');

export default function FaceAuthScreen() {
  const navigation = useNavigation();
  const { user, setFaceVerified } = useAuthStore();
  const device = useCameraDevice('front');
  const { hasPermission, requestPermission } = useCameraPermission();
  const { detectFaces } = useFaceDetector();
  
  const [isProcessing, setIsProcessing] = useState(false);
  const [status, setStatus] = useState<'scanning' | 'detected' | 'verifying' | 'success' | 'failed'>('scanning');
  const [progress, setProgress] = useState(0);
  
  const scanAnimation = useSharedValue(0);
  const pulseAnimation = useSharedValue(1);
  
  const faceDB = useRef<{ studentId: string; descriptor: number[]; name: string }[]>([]);
  
  useEffect(() => {
    loadFaceDatabase();
    scanAnimation.value = withRepeat(
      withTiming(1, { duration: 2000 }),
      -1,
      true
    );
    pulseAnimation.value = withRepeat(
      withSpring(1.2, { damping: 10 }),
      -1,
      true
    );
  }, []);

  const loadFaceDatabase = async () => {
    const { data, error } = await supabase
      .from('students')
      .select('id, name, face_descriptor');
    
    if (data) {
      faceDB.current = data
        .filter(s => s.face_descriptor)
        .map(s => ({
          studentId: s.id,
          name: s.name,
          descriptor: s.face_descriptor as number[],
        }));
    }
  };

  const handleFaceDetected = Worklets.createRunOnJS((faces: any[]) => {
    if (isProcessing || faces.length === 0) return;
    
    const face = faces[0];
    if (face.confidence > 0.8) {
      setStatus('detected');
      verifyFace(face);
    }
  });

  const verifyFace = async (faceData: any) => {
    setIsProcessing(true);
    setStatus('verifying');
    
    try {
      // Animate progress
      const progressInterval = setInterval(() => {
        setProgress(p => Math.min(p + 0.1, 0.9));
      }, 200);

      // Extract features and match
      const features = await extractFaceFeatures(faceData);
      const match = findBestMatch(features, faceDB.current);
      
      clearInterval(progressInterval);
      setProgress(1);

      if (match.match && match.studentId === user?.student_id) {
        setStatus('success');
        setFaceVerified(true);
        
        // Mark attendance
        await markAttendance(match.studentId);
        
        setTimeout(() => {
          navigation.navigate('StudentDashboard' as never);
        }, 1500);
      } else {
        setStatus('failed');
        setTimeout(() => {
          setStatus('scanning');
          setIsProcessing(false);
          setProgress(0);
        }, 2000);
      }
    } catch (error) {
      console.error('Face verification error:', error);
      setStatus('failed');
      setIsProcessing(false);
    }
  };

  const markAttendance = async (studentId: string) => {
    // Find open session for student's class
    const { data: session } = await supabase
      .from('sessions')
      .select('id')
      .eq('class_id', user?.students?.class_id)
      .eq('is_open', true)
      .eq('date', new Date().toISOString().split('T')[0])
      .single();

    if (session) {
      await supabase
        .from('attendance')
        .upsert({
          session_id: session.id,
          student_id: studentId,
          status: 'present',
          timestamp: new Date().toISOString(),
          verified_by_face: true,
        });
    }
  };

  const frameProcessor = useFrameProcessor((frame) => {
    'worklet';
    const faces = detectFaces(frame);
    if (faces.length > 0) {
      runOnJS(handleFaceDetected)(faces);
    }
  }, [handleFaceDetected]);

  const scanStyle = useAnimatedStyle(() => ({
    transform: [{ translateY: interpolate(scanAnimation.value, [0, 1], [0, 200]) }],
  }));

  const pulseStyle = useAnimatedStyle(() => ({
    transform: [{ scale: pulseAnimation.value }],
    opacity: interpolate(pulseAnimation.value, [1, 1.2], [0.6, 0]),
  }));

  if (!hasPermission) {
    return (
      <View className="flex-1 bg-slate-900 items-center justify-center p-6">
        <Text className="text-white text-lg mb-4">Camera permission required</Text>
        <GlassmorphismCard onPress={requestPermission}>
          <Text className="text-white font-semibold">Grant Permission</Text>
        </GlassmorphismCard>
      </View>
    );
  }

  if (device == null) {
    return (
      <View className="flex-1 bg-slate-900 items-center justify-center">
        <Text className="text-white">No front camera available</Text>
      </View>
    );
  }

  return (
    <View className="flex-1 bg-slate-900">
      <Camera
        style={StyleSheet.absoluteFill}
        device={device}
        isActive={true}
        frameProcessor={frameProcessor}
        pixelFormat="rgb"
      />
      
      {/* Overlay UI */}
      <View className="flex-1 justify-center items-center">
        {/* Face frame guide */}
        <View className="w-72 h-72 rounded-3xl border-2 border-cyan-400/50 items-center justify-center overflow-hidden">
          <Animated.View 
            className="absolute w-full h-1 bg-cyan-400/80 shadow-lg shadow-cyan-400/50"
            style={scanStyle}
          />
          <Animated.View 
            className="absolute w-full h-full rounded-3xl border-2 border-cyan-400"
            style={pulseStyle}
          />
          
          {/* Corner markers */}
          <View className="absolute top-0 left-0 w-8 h-8 border-t-4 border-l-4 border-neon-blue rounded-tl-xl" />
          <View className="absolute top-0 right-0 w-8 h-8 border-t-4 border-r-4 border-neon-blue rounded-tr-xl" />
          <View className="absolute bottom-0 left-0 w-8 h-8 border-b-4 border-l-4 border-neon-blue rounded-bl-xl" />
          <View className="absolute bottom-0 right-0 w-8 h-8 border-b-4 border-r-4 border-neon-blue rounded-br-xl" />
        </View>

        {/* Status Card */}
        <GlassmorphismCard className="mt-8 px-8 py-4">
          {status === 'scanning' && (
            <Text className="text-cyan-400 text-lg font-semibold">Position face in frame</Text>
          )}
          {status === 'detected' && (
            <Text className="text-yellow-400 text-lg font-semibold">Face detected...</Text>
          )}
          {status === 'verifying' && (
            <View className="items-center">
              <ActivityIndicator color="#00f3ff" className="mb-2" />
              <Text className="text-cyan-400">Verifying identity...</Text>
              <View className="w-48 h-2 bg-slate-700 rounded-full mt-2 overflow-hidden">
                <Animated.View 
                  className="h-full bg-neon-blue"
                  style={{ width: `${progress * 100}%` }}
                />
              </View>
            </View>
          )}
          {status === 'success' && (
            <Text className="text-neon-green text-lg font-bold">✓ Verified! Welcome back</Text>
          )}
          {status === 'failed' && (
            <Text className="text-red-500 text-lg font-bold">✗ Verification failed</Text>
          )}
        </GlassmorphismCard>

        {/* Instructions */}
        <Text className="text-slate-400 mt-6 text-center px-8">
          Look directly at the camera. Ensure good lighting and remove glasses if possible.
        </Text>
      </View>
    </View>
  );
}