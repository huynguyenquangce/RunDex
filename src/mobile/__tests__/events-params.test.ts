import { PAGE_SIZE, toQueryParams } from '@/api/events';

describe('toQueryParams', () => {
  it('drops empty filters and applies the default page size', () => {
    expect(toQueryParams({})).toEqual({
      q: undefined,
      type: undefined,
      distance: undefined,
      region: undefined,
      from: undefined,
      to: undefined,
      open_only: undefined,
      include_past: undefined,
      limit: PAGE_SIZE,
      cursor: undefined,
    });
  });

  it('trims the search text and maps UI names to API names', () => {
    const params = toQueryParams(
      { q: '  đà lạt ', type: 'trail', distance: ['42', 'ultra'], openOnly: true },
      'abc',
      10,
    );
    expect(params).toMatchObject({
      q: 'đà lạt',
      type: 'trail',
      distance: ['42', 'ultra'],
      open_only: true,
      limit: 10,
      cursor: 'abc',
    });
  });

  it('treats a blank search and an empty distance list as no filter', () => {
    const params = toQueryParams({ q: '   ', distance: [] });
    expect(params.q).toBeUndefined();
    expect(params.distance).toBeUndefined();
  });
});
