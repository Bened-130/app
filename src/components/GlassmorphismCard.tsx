import React from 'react';
import { TouchableOpacity, View, ViewStyle } from 'react-native';
import Animated, { 
  useAnimatedStyle, withSpring, useSharedValue 
} from 'react-native-reanimated';

interface Props {
  children: React.ReactNode;
  onPress?: () => void;
  className?: string;
  style?: ViewStyle;
  activeScale?: number;
}

const AnimatedTouchable = Animated.createAnimatedComponent(TouchableOpacity);

export default function GlassmorphismCard({ 
  children, 
  onPress, 
  className = '', 
  style,
  activeScale = 0.98 
}: Props) {
  const scale = useSharedValue(1);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  const handlePressIn = () => {
    scale.value = withSpring(activeScale, { damping: 15 });
  };

  const handlePressOut = () => {
    scale.value = withSpring(1, { damping: 15 });
  };

  const Container = onPress ? AnimatedTouchable : View;
  const containerProps = onPress ? {
    onPress,
    onPressIn: handlePressIn,
    onPressOut: handlePressOut,
    activeOpacity: 0.9,
  } : {};

  return (
    <Container
      {...containerProps}
      style={[
        {
          backgroundColor: 'rgba(255, 255, 255, 0.08)',
          backdropFilter: 'blur(20px)',
          borderRadius: 20,
          borderWidth: 1,
          borderColor: 'rgba(255, 255, 255, 0.15)',
          shadowColor: '#000',
          shadowOffset: { width: 0, height: 8 },
          shadowOpacity: 0.3,
          shadowRadius: 20,
          elevation: 10,
        },
        animatedStyle,
        style,
      ]}
      className={`p-4 ${className}`}
    >
      {children}
    </Container>
  );
}