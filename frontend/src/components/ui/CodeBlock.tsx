import React, { useState } from 'react';
import { Box, IconButton, Paper, Tooltip, Typography } from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckIcon from '@mui/icons-material/Check';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/cjs/styles/prism';

interface CodeBlockProps {
  code: string;
  language?: string;
  showLineNumbers?: boolean;
  title?: string;
}

const CodeBlock: React.FC<CodeBlockProps> = ({
  code,
  language = 'javascript',
  showLineNumbers = true,
  title,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Paper
      elevation={3}
      sx={{
        my: 2,
        position: 'relative',
        overflow: 'hidden',
        borderRadius: 1,
      }}
    >
      {title && (
        <Box
          sx={{
            px: 2,
            py: 1,
            backgroundColor: 'grey.900',
            borderBottom: '1px solid',
            borderColor: 'grey.800',
          }}
        >
          <Typography variant="body2" color="grey.300">
            {title}
          </Typography>
        </Box>
      )}

      <IconButton
        size="small"
        onClick={handleCopy}
        sx={{
          position: 'absolute',
          top: title ? 48 : 8,
          right: 8,
          backgroundColor: 'rgba(0, 0, 0, 0.3)',
          color: 'grey.300',
          '&:hover': {
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
          },
          zIndex: 1,
        }}
      >
        <Tooltip title={copied ? '복사됨!' : '클립보드에 복사'}>
          {copied ? <CheckIcon fontSize="small" /> : <ContentCopyIcon fontSize="small" />}
        </Tooltip>
      </IconButton>

      <Box sx={{ fontSize: '0.9rem' }}>
        <SyntaxHighlighter
          language={language}
          style={vscDarkPlus}
          showLineNumbers={showLineNumbers}
          customStyle={{ margin: 0, borderRadius: 0 }}
        >
          {code}
        </SyntaxHighlighter>
      </Box>
    </Paper>
  );
};

export default CodeBlock;
