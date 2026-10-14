-- Seed data for local development and demos.
-- Categories and products only; user and interaction data is created at runtime.

insert into public.categories (name, slug, description) values
  ('Audio', 'audio', 'Headphones, speakers, and audio accessories.'),
  ('Computers', 'computers', 'Laptops, desktops, and computing peripherals.'),
  ('Mobile', 'mobile', 'Smartphones, tablets, and mobile accessories.'),
  ('Wearables', 'wearables', 'Smart watches, trackers, and wearable technology.'),
  ('Home', 'home', 'Smart home and everyday home electronics.')
on conflict (slug) do update
  set name = excluded.name,
      description = excluded.description;

insert into public.products (category_id, name, description, price, image_url, is_active)
select c.id, p.name, p.description, p.price, p.image_url, true
from (
  values
    ('audio', 'Aurora Wireless Headphones', 'Over-ear active noise cancelling headphones.', 249.99, 'https://example.com/images/aurora-headphones.jpg'),
    ('audio', 'Pulse Bluetooth Speaker', 'Portable waterproof speaker with deep bass.', 89.50, 'https://example.com/images/pulse-speaker.jpg'),
    ('audio', 'Echo Studio Earbuds', 'Compact true wireless earbuds with long battery life.', 129.00, 'https://example.com/images/echo-earbuds.jpg'),
    ('computers', 'Nimbus 14 Laptop', 'Lightweight 14-inch laptop for everyday work.', 1099.00, 'https://example.com/images/nimbus-14.jpg'),
    ('computers', 'Vertex Mechanical Keyboard', 'Tactile mechanical keyboard with backlighting.', 119.99, 'https://example.com/images/vertex-keyboard.jpg'),
    ('computers', 'Clarity 27 Monitor', '27-inch QHD monitor for productivity.', 329.00, 'https://example.com/images/clarity-27.jpg'),
    ('mobile', 'Solstice Smartphone', 'Flagship smartphone with a high refresh display.', 899.00, 'https://example.com/images/solstice-phone.jpg'),
    ('mobile', 'Drift Tablet 11', '11-inch tablet for reading, media, and notes.', 449.00, 'https://example.com/images/drift-tablet.jpg'),
    ('mobile', 'Anchor Fast Charger', '65W USB-C fast charger for phones and laptops.', 39.99, 'https://example.com/images/anchor-charger.jpg'),
    ('wearables', 'Pulse Smartwatch', 'Fitness and health tracking smartwatch.', 199.00, 'https://example.com/images/pulse-watch.jpg'),
    ('wearables', 'Stride Running Tracker', 'Lightweight activity tracker for runners.', 79.00, 'https://example.com/images/stride-tracker.jpg'),
    ('home', 'Hearth Smart Bulb Pack', 'Colour smart bulb four-pack with app control.', 59.99, 'https://example.com/images/hearth-bulbs.jpg'),
    ('home', 'Haven Smart Plug', 'Wi-Fi smart plug with energy monitoring.', 24.99, 'https://example.com/images/haven-plug.jpg')
) as p (category_slug, name, description, price, image_url)
join public.categories c on c.slug = p.category_slug
on conflict do nothing;