   alter table profiles
     add column role text not null default 'user'
     check (role in ('user', 'admin'));