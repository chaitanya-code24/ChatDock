// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, GithubAuthProvider } from "firebase/auth";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyAGn_OLFEpzgUGdC1XplU4ERALfXeoTeeg",
  authDomain: "hundred-percent.firebaseapp.com",
  projectId: "hundred-percent",
  storageBucket: "hundred-percent.appspot.com",
  messagingSenderId: "421996787951",
  appId: "1:421996787951:web:c181f035063d4dc592831a",
  measurementId: "G-REP68S4KNN"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);


const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();
const githubProvider = new GithubAuthProvider();

export { auth, googleProvider, githubProvider };