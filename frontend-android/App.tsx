import React, { useEffect } from 'react';
import { StatusBar, LogBox } from 'react-native';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { RootStackParamList } from './src/types';
import HomeScreen from './src/screens/HomeScreen';
import TaskSelectionScreen from './src/screens/TaskSelectionScreen';
import TimerScreen from './src/screens/TimerScreen';
import theme from './src/theme/theme';
import CreateTaskScreen from './src/screens/CreateTaskScreen';

// Ignore specific warnings that are not relevant or can't be fixed
LogBox.ignoreLogs([
  'Non-serializable values were found in the navigation state',
]);

// Create navigation stack
const Stack = createStackNavigator<RootStackParamList>();

// Define navigation theme matching our app theme
const NavigationTheme = {
  ...DefaultTheme,
  dark: true,
  colors: {
    ...DefaultTheme.colors,
    primary: theme.colors.primary,
    background: theme.colors.background,
    card: theme.colors.card,
    text: theme.colors.text,
    border: theme.colors.divider,
  },
};

const App: React.FC = () => {
  return (
    <NavigationContainer theme={NavigationTheme}>
      <StatusBar
        barStyle="light-content"
        backgroundColor={theme.colors.background}
        translucent={false}
      />
      
      <Stack.Navigator
        initialRouteName="Home"
        screenOptions={{
          headerShown: false,
          cardStyle: { backgroundColor: theme.colors.background },
        }}
      >
        <Stack.Screen name="Home" component={HomeScreen} />
        <Stack.Screen name="TaskSelection" component={TaskSelectionScreen} />
        <Stack.Screen name="Timer" component={TimerScreen} />
        <Stack.Screen name="CreateTask" component={CreateTaskScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default App; 