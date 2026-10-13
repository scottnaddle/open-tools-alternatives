export type FloatingInputProps = {
  id: string;
  label: string;
  type: string;
  placeholder: string;
  required: boolean;
};

export type QuickChipsAppItem = {
  id: string;
  data: {
    name: string;
  };
};

export type QuickChipsProps = {
  apps: QuickChipsAppItem[];
  base: string;
};

export type SearchIndexItem = {
  id: string;
  name: string;
  syn: string[];
  n: number;
};

export type SearchAutocompleteProps = {
  index: SearchIndexItem[];
  base: string;
};
