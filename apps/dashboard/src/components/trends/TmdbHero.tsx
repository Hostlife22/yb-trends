import { useState } from 'react';
import { Star, Clock, Calendar, Globe2, Film, ExternalLink } from 'lucide-react';
import clsx from 'clsx';
import type { ClassifiedTrendItem } from '@/api/types';
import Badge from '@/components/ui/Badge';

const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p';
const POSTER_SIZE = 'w500';
const BACKDROP_SIZE = 'w1280';

interface TmdbHeroProps {
  item: ClassifiedTrendItem;
}

type TmdbDetails = {
  poster_path?: string;
  backdrop_path?: string;
  overview?: string;
  tagline?: string;
  homepage?: string;
  release_date?: string;
  first_air_date?: string;
  runtime?: number;
  number_of_seasons?: number;
  number_of_episodes?: number;
  vote_average?: number;
  vote_count?: number;
  status?: string;
  spoken_languages?: string[];
  production_countries?: string[];
  popularity?: number;
  media_type?: string;
};

function formatRuntime(minutes?: number): string | null {
  if (!minutes || minutes <= 0) return null;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h === 0) return `${m}m`;
  if (m === 0) return `${h}h`;
  return `${h}h ${m}m`;
}

function formatDate(iso?: string): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  return d.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
}

export default function TmdbHero({ item }: TmdbHeroProps) {
  const details = (item.tmdb_details ?? null) as TmdbDetails | null;
  const [posterError, setPosterError] = useState(false);

  const posterUrl = details?.poster_path
    ? `${TMDB_IMAGE_BASE}/${POSTER_SIZE}${details.poster_path}`
    : null;
  const backdropUrl = details?.backdrop_path
    ? `${TMDB_IMAGE_BASE}/${BACKDROP_SIZE}${details.backdrop_path}`
    : null;

  const releaseDate = formatDate(details?.release_date ?? details?.first_air_date);
  const runtime = formatRuntime(details?.runtime);
  const rating = details?.vote_average;
  const voteCount = details?.vote_count;
  const homepage = details?.homepage;
  const tmdbUrl = item.tmdb_id
    ? `https://www.themoviedb.org/${details?.media_type === 'tv' ? 'tv' : 'movie'}/${item.tmdb_id}`
    : null;

  if (!details && !item.tmdb_id) {
    // Nothing TMDB-derived to show — let the page fall back to TrendMeta only.
    return null;
  }

  return (
    <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/5">
      {backdropUrl && (
        <div
          aria-hidden
          className="absolute inset-0 bg-cover bg-center opacity-25"
          style={{ backgroundImage: `url(${backdropUrl})` }}
        />
      )}
      <div
        aria-hidden
        className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent"
      />

      <div className="relative flex flex-col gap-6 p-6 md:flex-row md:p-8">
        {/* Poster */}
        <div className="shrink-0">
          {posterUrl && !posterError ? (
            <img
              src={posterUrl}
              alt={item.title_normalized}
              className="h-[300px] w-[200px] rounded-xl object-cover shadow-2xl ring-1 ring-white/10"
              onError={() => setPosterError(true)}
              loading="lazy"
            />
          ) : (
            <div className="flex h-[300px] w-[200px] items-center justify-center rounded-xl bg-white/5 ring-1 ring-white/10">
              <Film className="h-16 w-16 text-white/20" />
            </div>
          )}
        </div>

        {/* Info */}
        <div className="flex min-w-0 flex-1 flex-col justify-between gap-4">
          <div className="flex flex-col gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={item.content_type}>{item.content_type}</Badge>
              {item.studio && item.studio !== 'unknown' && (
                <span className="text-sm text-gray-300">{item.studio}</span>
              )}
              {item.release_year && (
                <span className="text-sm text-gray-400">· {item.release_year}</span>
              )}
            </div>

            {details?.tagline && (
              <p className="text-sm italic text-gray-400">"{details.tagline}"</p>
            )}

            {details?.overview && (
              <p className="text-sm leading-relaxed text-gray-200 md:text-base">
                {details.overview}
              </p>
            )}
          </div>

          {/* Quick facts grid */}
          <div className="flex flex-wrap items-center gap-x-5 gap-y-3 text-sm">
            {typeof rating === 'number' && rating > 0 && (
              <span className="flex items-center gap-1.5 text-amber-300">
                <Star className="h-4 w-4 fill-amber-300" />
                <span className="font-semibold">{rating.toFixed(1)}</span>
                {typeof voteCount === 'number' && voteCount > 0 && (
                  <span className="text-xs text-gray-500">
                    ({voteCount.toLocaleString()} votes)
                  </span>
                )}
              </span>
            )}
            {runtime && (
              <span className="flex items-center gap-1.5 text-gray-300">
                <Clock className="h-4 w-4 text-gray-500" />
                {runtime}
              </span>
            )}
            {!runtime && typeof details?.number_of_episodes === 'number' && (
              <span className="flex items-center gap-1.5 text-gray-300">
                <Clock className="h-4 w-4 text-gray-500" />
                {details.number_of_episodes} eps
                {typeof details.number_of_seasons === 'number'
                  ? ` · ${details.number_of_seasons} seasons`
                  : ''}
              </span>
            )}
            {releaseDate && (
              <span className="flex items-center gap-1.5 text-gray-300">
                <Calendar className="h-4 w-4 text-gray-500" />
                {releaseDate}
              </span>
            )}
            {item.original_language && (
              <span className="flex items-center gap-1.5 text-gray-300">
                <Globe2 className="h-4 w-4 text-gray-500" />
                <span className="uppercase">{item.original_language}</span>
                {item.origin_country && (
                  <span className="text-gray-500">· {item.origin_country}</span>
                )}
              </span>
            )}
            {details?.status && (
              <span className="rounded-full bg-white/10 px-2 py-0.5 text-xs text-gray-300">
                {details.status}
              </span>
            )}
          </div>

          {/* Genres */}
          {item.genres && item.genres.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {item.genres.map((g) => (
                <span
                  key={g}
                  className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-gray-300"
                >
                  {g}
                </span>
              ))}
            </div>
          )}

          {/* External links */}
          {(tmdbUrl || homepage) && (
            <div className="flex flex-wrap items-center gap-3 text-xs">
              {tmdbUrl && (
                <a
                  href={tmdbUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={clsx(
                    'inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5',
                    'bg-white/10 text-gray-200 transition-colors hover:bg-white/20',
                  )}
                >
                  TMDB
                  <ExternalLink className="h-3 w-3" />
                </a>
              )}
              {homepage && (
                <a
                  href={homepage}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 bg-white/10 text-gray-200 transition-colors hover:bg-white/20"
                >
                  Homepage
                  <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
