import { InputAdornment, TextField } from '@mui/material';
import SearchIcon from '@mui/icons-material/SearchOutlined';
import { useStyles } from './SearchFieldStyles';

export interface SearchFieldProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  ariaLabel?: string;
  testId?: string;
}

export const SearchField = ({
  value,
  onChange,
  placeholder,
  ariaLabel,
  testId,
}: SearchFieldProps) => {
  const { classes } = useStyles();

  return (
    <TextField
      className={classes.root}
      type="search"
      size="small"
      value={value}
      placeholder={placeholder}
      inputProps={{ 'aria-label': ariaLabel ?? placeholder, 'data-testid': testId }}
      onChange={(event) => onChange(event.target.value)}
      InputProps={{
        startAdornment: (
          <InputAdornment position="start">
            <SearchIcon className={classes.icon} />
          </InputAdornment>
        ),
      }}
    />
  );
};
