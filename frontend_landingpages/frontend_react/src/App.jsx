import { useState } from 'react'
import './App.css'
import LoginForm from './pages/loginpage';

function App() {
  const [count, setCount] = useState(0)

  return <LoginForm count ={count} setCount = {setCount} />;
}

export default App;


