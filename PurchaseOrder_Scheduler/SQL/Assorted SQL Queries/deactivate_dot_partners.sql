select * from res_partner where left(name,1) = '.' and active = true;

update res_partner set active = false where id in (select id from res_partner where left(name,1) = '.' and active = true);