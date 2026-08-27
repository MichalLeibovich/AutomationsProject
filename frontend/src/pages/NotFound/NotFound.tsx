import { useNavigate } from 'react-router-dom';
import SearchOffIcon from '@mui/icons-material/SearchOffOutlined';
import { Button } from '@/components/Button/Button';
import { EmptyState } from '@/components/EmptyState/EmptyState';
import { he } from '@/locales/he';
import { paths } from '@/routes/paths';
import { useStyles } from './NotFoundStyles';

export const NotFound = () => {
  const { classes } = useStyles();
  const navigate = useNavigate();

  return (
    <div className={classes.root}>
      <EmptyState
        icon={<SearchOffIcon fontSize="inherit" />}
        title={he.errors.notFoundTitle}
        body={he.errors.notFoundBody}
        action={
          <Button variant="tint" onClick={() => navigate(paths.tests)}>
            {he.errors.backHome}
          </Button>
        }
      />
    </div>
  );
};
