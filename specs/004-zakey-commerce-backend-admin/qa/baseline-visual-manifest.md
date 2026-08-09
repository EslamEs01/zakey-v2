# Baseline Visual Manifest — 004-zakey-commerce-backend-admin

Recorded at 2026-08-05T05:42Z (UTC). Snapshot directory:
`tests/visual/visual-regression.spec.js-snapshots/`

- Snapshot PNG count: **52** (13 public routes × 4 viewport projects)
- Chrome-only Playwright channel, Linux baselines, full-page captures,
  animations disabled, fonts settled before capture
  (see `tests/visual/visual-regression.spec.js`).

## Determinism evidence

- Baseline generation run (T-0102b):
  `npx playwright test ./tests/visual --project=chrome-1440 --project=chrome-1024 --project=chrome-768 --project=chrome-390 --update-snapshots`
  → summary line: `  52 passed (40.1s)`
- Verification run (no `--update-snapshots`, must pass with zero diffs):
  `npx playwright test ./tests/visual --project=chrome-1440 --project=chrome-1024 --project=chrome-768 --project=chrome-390`
  → summary line: `  52 passed (36.4s)`

## Routes covered (ids from tests/visual/visual-regression.spec.js)

`home`, `shop`, `collection`, `search`, `product`, `cart`, `checkout`,
`wishlist`, `account`, `about`, `contact`, `error-404`, `error-500`

## sha256 checksums

Generated via `sha256sum *.png | sort -k2` in the snapshot directory.

| Snapshot file | sha256 |
| --- | --- |
| `about-chrome-1024-linux.png` | `a13370449ae2070cb15a266f3fc3efe65d7816c96499085c927ec86315fc5d8d` |
| `about-chrome-1440-linux.png` | `a0241f1f1673fcf89fdc201d6182ecd20c131799d11ce0fb1fe44b2647cd348f` |
| `about-chrome-390-linux.png` | `8bf052547692c22eb1ccbcd597db1e9affc04835b40f8846d7929cbae58b0fa8` |
| `about-chrome-768-linux.png` | `1db59d0509a725945426ef3eb3175a52d9b745ce01bc16f851e0ee23c63e98ba` |
| `account-chrome-1024-linux.png` | `0a043cceb4af55b3ec243c631c1b39c02e5240077ca7df3d45e64779f9dbc8b9` |
| `account-chrome-1440-linux.png` | `7f7cd97f813033334bfecd5b32cffce2a6b0de92d62968054b9d1e8761c4ffef` |
| `account-chrome-390-linux.png` | `cc6ece4f97c640b5603242ecf6f5b097345a5af545a1d65af0671ae92148e5e0` |
| `account-chrome-768-linux.png` | `ed2c59498b5bbe21d465d97b595b9237c0e651df871c1b614b7173c1b447b8dc` |
| `cart-chrome-1024-linux.png` | `426c3e8236e6b46743f604c679db41db46b8157151953b14239dcaa7163c596a` |
| `cart-chrome-1440-linux.png` | `4148e24cf45beb55365ccaec74e58039223439739770e2c088928338c33a9839` |
| `cart-chrome-390-linux.png` | `50423ec79a554afe8f6caa3a4428a61838e25953b4158ecce02f8a8fd87a0882` |
| `cart-chrome-768-linux.png` | `c77e225deb75c472b49689739a1453c01f35cae3665b5f47b9bb0304ef98db3d` |
| `checkout-chrome-1024-linux.png` | `4001f6ae4ff91f18396d946039d019926c067c647e30a61318b2e622259ca474` |
| `checkout-chrome-1440-linux.png` | `a2d5aa283afbe601cb71b84e8ca2542d3007ef91eb23755b27436bed4678255b` |
| `checkout-chrome-390-linux.png` | `1f20fc7db5ff5f82781f05137413aa5fd59936e315496a6f57f24ec66dde27f1` |
| `checkout-chrome-768-linux.png` | `6c6fc5dedbbcc2b97a20ff1cb32e02f6854166a05b27c1ca720a6219bf3e8b7f` |
| `collection-chrome-1024-linux.png` | `33197cea58ee2c4055f3ea5f84f95a42fbcff432473aa0f3a0e8d2c1faee26cf` |
| `collection-chrome-1440-linux.png` | `a7cc5b77a47d055e75bac1e3a4bf38f9c500e971c87a2f54f7a1de8a71ac7e48` |
| `collection-chrome-390-linux.png` | `6cd1a202154b333908a33b7036856839cd4172ae3f71db747e6c53182d7aa4a6` |
| `collection-chrome-768-linux.png` | `bc99575b2d28762eade0bb6eb6fe1756cb5e3d3a0fc2db6eee3c5979bb37dee5` |
| `contact-chrome-1024-linux.png` | `b9c261c2c58bac2d02cde148063d983a82f1466ba1ae9ebadda59755cb5a8fee` |
| `contact-chrome-1440-linux.png` | `76edc9b194c2b5fe2e712ead97cfbf333870a7fc9cbe7b2dab82e5201802bb4b` |
| `contact-chrome-390-linux.png` | `68d556b8bac46fe684a5c0bfe8e360edcf3ef0ba76e7db2e52cf4e53762bd6aa` |
| `contact-chrome-768-linux.png` | `c935bf4ea58eb9c28bf0a79ba4629ebf1bffea9d2e769f661b29359c309c42f0` |
| `error-404-chrome-1024-linux.png` | `ce449ec02b8d53be26001a68dbc4772a98f28c757ba54be88bb3eaffc2f2e178` |
| `error-404-chrome-1440-linux.png` | `8145854070336502764f30d425632615a1a564684a2b0610b06cd996378d6e5b` |
| `error-404-chrome-390-linux.png` | `94d09c51fa4506b045e716829df0096667997f905d463596815bbd7a415115a3` |
| `error-404-chrome-768-linux.png` | `b3d9e4275329392658be180f838c11b1637e983bb5ca6a750ec44cfb6988563a` |
| `error-500-chrome-1024-linux.png` | `f0595f854b2329c0f685cffb82a35beed833568918fd165182aab19ac2565eae` |
| `error-500-chrome-1440-linux.png` | `5c52477ab9714a3496349063a75de12f5084ce7613fb60e1aae8899d5eb9df98` |
| `error-500-chrome-390-linux.png` | `e7876027b2da6fc15d29c17de84b95b7f123316b4cdb28914bad8821dd532495` |
| `error-500-chrome-768-linux.png` | `05733738d850777a2f074082ec84d74a52e026f54ced896c4ecb26d9ed993534` |
| `home-chrome-1024-linux.png` | `8cd84fded8be1385c212b38fcdc56438110151f90d339a0e5cd3c18c42314bb7` |
| `home-chrome-1440-linux.png` | `2fcac65f39979ba89f600f5b3379d97c9345387977686217f29a43648da35572` |
| `home-chrome-390-linux.png` | `1a516ed66676c5257d313ab0a10a30030cf3bac9e16e184ff1fe86ed60e96465` |
| `home-chrome-768-linux.png` | `91e3b03b433368f4b87dbc5495a7b3e5f974fd52581ca33bac203d0b259c0759` |
| `product-chrome-1024-linux.png` | `268af0a84c5ea4b6d1c7f35c3671191466a03e3790e757f34c8b92a79c729fc8` |
| `product-chrome-1440-linux.png` | `674c4f3315edc76016935a0c60406309a07fbdaaf29a336a4e9f88baeb200022` |
| `product-chrome-390-linux.png` | `7b53c9c9bc2b000cfb9e66aec1483b2f3248d3d9ecf2a5737bcefca4774c73bb` |
| `product-chrome-768-linux.png` | `5e88caa48a4d061336beef6fb7e7b4dc6cacf295285cbe65499a764af700a162` |
| `search-chrome-1024-linux.png` | `41f29d8e7c550ad9d902847b1167271d3639b9b9f2c1a8ae49a24fd064f79f8e` |
| `search-chrome-1440-linux.png` | `adbf2c47e4c3b0b684dd6cd4dfc1051969afc51ca554df33ed088d74ecb60da0` |
| `search-chrome-390-linux.png` | `733e17e9c4bc8a0381de04d6f629d3c458e412c69ab138776b8f1a50a6948738` |
| `search-chrome-768-linux.png` | `c9cd32bd1a77d1e57649b0ff151815bf69bfeabae04aa8e20ecf4cfa4821b775` |
| `shop-chrome-1024-linux.png` | `c1007901e1e1067dd5a7c78cdecd09c5e9252ae52498c6c2c2e012543895e5c8` |
| `shop-chrome-1440-linux.png` | `f87fdc600a789d58a760cec29dab34d017424033edf7d2473efd2a59a85b8a1d` |
| `shop-chrome-390-linux.png` | `188f05bfaccdec39dd8bdca34fdbe22801f276c9b1a9fff8f6c9d8e8d085e5c7` |
| `shop-chrome-768-linux.png` | `c5fd5e29f259d8c1d636811f79587ccf743c1214826124cf4fae9b8ea73a42ff` |
| `wishlist-chrome-1024-linux.png` | `e3cf1ead11e4d7420fac0b9e282afdd508d52c6de63c6dec3ef22fe1d1447255` |
| `wishlist-chrome-1440-linux.png` | `b2dfe397efca65a762e833fdb863da8137900f654d91f476f4034b4b00e3c673` |
| `wishlist-chrome-390-linux.png` | `f73497da66f6eb6a705bc09434cd29a671c6345a3c37340e5c187f5be53282f8` |
| `wishlist-chrome-768-linux.png` | `820480d110eae2541ab0311c039fa382e3e875525841af32b821ba57d9520416` |
