import React, { createContext, useContext, useEffect, useRef } from 'react';
import { View, Text, Animated, Dimensions } from 'react-native';
import { supabase } from '../lib/supabase';
import { useAuthStore } from '../store/authStore';
import { Notification } from '../types';
import { Ionicons } from '@expo/vector-icons';

const { width } = Dimensions.get('window');

interface NotificationContextType {
  showNotification: (notification: Notification) => void;
}

const NotificationContext = createContext<NotificationContextType | null>(null);

export const useRealtimeNotification = () => useContext(NotificationContext);

export function RealtimeNotificationProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuthStore();
  const [currentNotification, setCurrentNotification] = React.useState<Notification | null>(null);
  const slideAnim = useRef(new Animated.Value(-100)).current;

  useEffect(() => {
    if (!user) return;

    // Subscribe to notifications
    const subscription = supabase
      .channel('notifications')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'notifications',
          filter: `user_id=eq.${user.id}`,
        },
        (payload) => {
          const notification = payload.new as Notification;
          if (!notification.read) {
            showNotification(notification);
          }
        }
      )
      .subscribe();

    return () => {
      subscription.unsubscribe();
    };
  }, [user]);

  const showNotification = (notification: Notification) => {
    setCurrentNotification(notification);
    
    Animated.sequence([
      Animated.spring(slideAnim, {
        toValue: 50,
        useNativeDriver: true,
        friction: 8,
      }),
      Animated.delay(4000),
      Animated.timing(slideAnim, {
        toValue: -150,
        duration: 300,
        useNativeDriver: true,
      }),
    ]).start(() => setCurrentNotification(null));
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'payment': return 'cash-outline';
      case 'assignment': return 'document-text-outline';
      case 'attendance': return 'checkmark-circle-outline';
      case 'comment': return 'chatbubble-outline';
      default: return 'notifications-outline';
    }
  };

  return (
    <NotificationContext.Provider value={{ showNotification }}>
      {children}
      {currentNotification && (
        <Animated.View
          className="absolute top-0 left-4 right-4 bg-glass-dark backdrop-blur-xl rounded-2xl p-4 border border-white/20 shadow-2xl"
          style={{
            transform: [{ translateY: slideAnim }],
            zIndex: 1000,
          }}
        >
          <View className="flex-row items-center">
            <View className="w-10 h-10 rounded-full bg-neon-blue/20 items-center justify-center mr-3">
              <Ionicons 
                name={getIcon(currentNotification.type)} 
                size={20} 
                color="#00f3ff" 
              />
            </View>
            <View className="flex-1">
              <Text className="text-white font-bold text-sm">
                {currentNotification.title}
              </Text>
              <Text className="text-slate-300 text-xs mt-1">
                {currentNotification.message}
              </Text>
            </View>
          </View>
        </Animated.View>
      )}
    </NotificationContext.Provider>
  );
}