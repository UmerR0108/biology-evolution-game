# Assets

Provenance and licensing for the third-party art used in this project.

## tilesets/free_version/

Source: free download from author "shubibubi" (see `read me.txt` shipped in the pack).
Used for: terrain tiles (grass, water corners), tree, cottage, character sprite.

## fish/NewRiverFishAssetPack1.0/

Source: New River Fish Asset Pack 1.0.
Used for: pond fish (guppies are tinted variants of one base fish silhouette).

## animals/MinifolksForestAnimals/

Source: Minifolks Forest Animals pack.
Used for: ambient wildlife (bunny in MVP; bird/deer/etc. deferred).

## characters/lablady/

Source: lab-lady spritesheet (boxed). Contains IDLE/WALK/RUN/PUSH/CLIMB/TALK
animation rows in 4 directions plus portrait frames.
Used for: the player character (field researcher).

## tilesets/water_plus/

Source: Water+ tileset. Animated water frames, shoreline edges, and water
decorations.
Used for: pond water tiles.

## trees/tree_pack/

Source: 15-tree pixel-art pack with multiple color variants per tree.
Used for: forest tree objects (Tree 6 = tall classic, Tree 9 = large round, Tree 11 = small pine).

## nature/

Source: NatureTiles composite tilesheet — vines, mushrooms, flowers, bushes,
small grass tufts. Used for: ambient forest decoration objects.

## water/

Source: wateranimate2.png — animated waterfall frames (currently unused) and
composite pond-with-grass-border tile used to render the pond as a single
sprite over the grass tilemap.

If you replace this folder with a different forest tileset, update the slice
rectangles in `src/evogame/ui/assets.py`.
