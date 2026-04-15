import React, { useRef, useEffect } from 'react';
import { View, StyleSheet } from 'react-native';
import { Video, ResizeMode } from 'expo-av';
import { useVideoPlayer, VideoView } from 'expo-video';

// Using expo-av for video background
export default function VideoBackground() {
  const video = useRef<Video>(null);

  useEffect(() => {
    (async () => {
      if (video.current) {
        await video.current.playAsync();
        video.current.setIsLoopingAsync(true);
      }
    })();
  }, []);

  return (
    <View style={StyleSheet.absoluteFill}>
      <Video
        ref={video}
        source={{ uri: 'https://assets.mixkit.co/videos/preview/mixkit-abstract-technology-network-connections-27611-large.mp4' }}
        style={StyleSheet.absoluteFill}
        resizeMode={ResizeMode.COVER}
        isLooping
        shouldPlay
        isMuted
      />
      {/* Dark overlay for readability */}
      <View className="absolute inset-0 bg-slate-900/70" />
      {/* Gradient overlay */}
      <View 
        className="absolute inset-0"
        style={{
          background: 'linear-gradient(180deg, rgba(15, 23, 42, 0.3) 0%, rgba(15, 23, 42, 0.9) 100%)',
        }}
      />
    </View>
  );
}