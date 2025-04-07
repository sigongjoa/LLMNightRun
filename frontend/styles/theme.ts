import { createTheme } from '@mui/material/styles';

// LLMNightRun 테마 설정
const theme = createTheme({
  palette: {
    primary: {
      main: '#3f51b5', // 인디고
    },
    secondary: {
      main: '#f50057', // 핑크
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
      '"Apple Color Emoji"',
      '"Segoe UI Emoji"',
      '"Segoe UI Symbol"',
    ].join(','),
  },
  components: {
    MuiAppBar: {
      defaultProps: {
        elevation: 1,
      },
    },
    MuiCard: {
      defaultProps: {
        elevation: 2,
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
        },
      },
    },
  },
});

export default theme;
