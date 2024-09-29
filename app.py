# -*- coding: utf-8 -*-
from flask import Flask, render_template,request,redirect,url_for,session,flash # For flask implementation
from flask_wtf.csrf import CSRFProtect
from bson import ObjectId # For ObjectId to work
from pymongo import MongoClient
import os
from dotenv import load_dotenv



app = Flask(__name__)
csrf = CSRFProtect()
csrf.init_app(app) # Compliant
#parametro 
app.secret_key=os.getenv('key')
titulo = "PROYECTO"
encabezado = " Iniciar Sesion "

PRODUCTOS_COLLECTION = '$Productos'
pipeline_match = "$match"
consulta_project = "$project"
pipeline_unwind = "$unwind"
mensaje_registrado_exitoso = "Registrado con exito"
mensaje_update_exitoso = "Update con exito"
direccion_pedidos_disponibles = "/mostrarPedidosDisp/"

conex = MongoClient("mongodb://127.0.0.1:27017") #host uri
bd = conex.Prueba_Proyecto_Final   #Select the database
clientes = bd.clientes #Select the collection name
negocios=bd.negocios
repartidores=bd.repartidores
pedidos=bd.pedidos   
contador=bd.contador  
DicProductos = {}

@app.route("/", methods=['GET'])
def mostrar_login():
    return render_template("IniciarSesion.html")

@app.route("/login", methods=['POST'])
def login():
    ci_usuario = request.values.get("ci_usuario")
    id_usuario = int(ci_usuario)
    passw = request.values.get("contra_usuario")
    
    cliente = clientes.find({"_id": id_usuario})
    lista_cliente = list(cliente)

    if len(lista_cliente) != 0:
        cliente = lista_cliente[0]  
        if cliente["_id"] == id_usuario and cliente["contraCli"] == passw:
            return redirect(f"/mostrarCats/{id_usuario}")
        else:
            return redirect("/")  
    else:
        return redirect("/")

@app.route("/mostrarCats/<id>/", methods=['GET'])
def mostrar_cats(id):
    id_usuario=int(id)
    cliente_l=clientes.find({"_id":id_usuario})
    #print("Id: ",cliente_l[0]["_id"]," pass:",cliente_l[0]["contraCli"])
    return render_template("Categorias.html",cliente=cliente_l)

@app.route("/datosCliente/<id>/", methods=['GET'])
def datos_cliente(_id):
    _id=int(_id)
    cliente_l=clientes.find({"_id":_id})
    print("Id: ",cliente_l[0]["_id"]," pass:",cliente_l[0]["contraCli"])
    return render_template("DatosCliente.html",cliente=cliente_l)

@app.route("/mostrarNegs/<id>/",methods=['GET']) #get para mandar 
@app.route("/mostrarNegs/<id>/<categoria>/",methods=['GET']) #get para mandar 
def mostrar_negs(_id,categoria=None):
    DicProductos.clear()
    #print("Id: ",id)
    _id=int(_id)
    cliente_l=clientes.find({"_id":_id})
    if(categoria != None):
        negocios_l=negocios.find({"Categoria":categoria})
    else:
        negocios_l=negocios.find()
    #print("Id: ",cliente_l[0]["_id"]," pass:",cliente_l[0]["contraCli"])
    return render_template("negocios.html",cliente=cliente_l,negocios=negocios_l,categoria=categoria)

@app.route("/buscar/<id>/",methods=['GET'])
def buscar (_id):    
    _id=int(_id)
    criterio=request.values.get("search")
    categoria=request.values.get("categoria")
    cliente=clientes.find({"_id":_id})
    if(categoria != None):
        negocios_l=negocios.find({"Nombre":criterio,"Categoria":categoria})
    else:
        negocios_l=negocios.find({"Nombre":criterio})
    return render_template("negocios.html",cliente=cliente,negocios=negocios_l,categoria=categoria)

############################# PARTE MIA JUAN PABLO ############################


@app.route("/mostrarProds/<idCli>/<float:idNeg>/",methods=['GET'])
def mostrar_prods (id_cli,id_neg):  

    id_cli=int(id_cli)
    id_neg = float(id_neg)
    cliente_p=clientes.find({"_id":id_cli})
    negocio_p=negocios.find({"_id":id_neg})
    pipeline = [{pipeline_match:{"_id":id_neg}},{pipeline_unwind:PRODUCTOS_COLLECTION},{pipeline_match:{"Productos.Estado":"Disponible"}},{pipeline_match:{"_id":0,"Productos":1}}]  
    productos_p=list(negocios.aggregate(pipeline))
    return render_template("Productos.html",cliente=cliente_p,negocio=negocio_p,productos=productos_p)

def validar_producto(estado):
    if (estado == "No Disponible"):
        return False
    else:
        return True
                      

def remover_producto(id_prod, cantidad):
    if(len(DicProductos)>0 and id_prod in DicProductos and DicProductos[id_prod][0]>1):
            DicProductos[id_prod][0]+=cantidad
    else:
        DicProductos.pop(id_prod)

def actualizar_cantidad(id_prod, cantidad):
    ar = DicProductos[id_prod]
    ar[0]+=cantidad
    DicProductos[id_prod]=ar
    

def agregar_nuevo_producto(id_cli, id_neg, id_prod, cantidad):
    id_cli=int(id_cli)
    id_neg=float(id_neg)
    negocio_p=negocios.find({"_id":id_neg})
    prod_nom=negocio_p[0]["Nombre"]
    id_prod = float(id_prod)
    cantidad = int(cantidad)
    pipeline = [{pipeline_match:{"_id":id_neg}},{pipeline_unwind:PRODUCTOS_COLLECTION},{pipeline_match:{"Productos.cod_prod":id_prod}},{consulta_project:{"_id":0,"nombre_prod":"$Productos.Nombre","Precio":"$Productos.Precio","Productos":1}}]  
    producto=list(negocios.aggregate(pipeline))
    for produ in producto:
        prod_nom=produ["nombre_prod"]
        precio_prod=produ["Precio"]
    print(prod_nom,precio_prod)
    arry=[cantidad,precio_prod,prod_nom]
    DicProductos[id_prod] = arry

def agregar_producto(id_prod, cantidad, estado, id_cli, id_neg):
    if (validar_producto(estado) == True and id_prod in DicProductos):
        actualizar_cantidad(id_prod, cantidad)
    else:
        agregar_nuevo_producto(id_cli, id_neg, id_prod, cantidad)

        

@app.route("/AgregarProd/<idCli>/<float:idNeg>/<float:id_prod>/<cantidad>/<estado>",methods=['POST'])   
def leer_producto(id_cli,id_neg,id_prod,cantidad,estado):
    cantidad=int(cantidad)
    if(cantidad==1):
        agregar_producto(id_prod, cantidad, estado, id_cli, id_neg)
    elif(cantidad==-1):
        remover_producto(id_prod, cantidad)
    print(DicProductos) 
    return redirect(request.referrer)

###################################################################################


################################## PARTE ADRIAN ##################################

@app.route("/mostrarPedido/<idCli>/<float:idNeg>/",methods=['GET'])
def mostrar_pedido (id_cli,id_neg):    
    id_cli=int(id_cli)
    id_neg=float(id_neg)
    cliente=clientes.find({"_id":id_cli})
    negocio=negocios.find({"_id":id_neg})
    total=calcular_total()
    if (len(DicProductos)) == 0:
        return redirect(request.referrer)
    else:
        return render_template("MisPedidos.html",cliente=cliente, negocio=negocio, productos=DicProductos,total=total)

def calcular_total ():    
    total = 0
    for producto in DicProductos:
        total = total + (DicProductos[producto][0] * DicProductos[producto][1])
    return total
 
@app.route("/insertarPedido/<idCli>/<float:idNeg>/",methods=['GET'])
def insertar_pedido (id_cli,id_neg):    
    id_cli=int(id_cli)
    id_neg=float(id_neg)
    total=calcular_total()
    cliente=clientes.find({"_id":id_cli})
    negocio=negocios.find({"_id":id_neg})

    repartidor=repartidores.find({"estado":"D"})
    if len(list(repartidor))!= 0:
        repartidor=repartidores.find({"estado":"D"})
        id_rep=repartidor[0]["_id"]
        
        cont=contador.find({"_id":1})
        valor=cont[0]["contador"]
        pedidos.insert_one({"_id":valor,"estado_ped":"pendiente","montoTotal":total,"cliente":id_cli,"negocioId":id_neg,"repartidorId":id_rep,"productos":[]})
        for producto in DicProductos:
            pedidos.update_one({"_id":valor},{"$push":{"productos":{'cod_prod':producto,'Nombre':DicProductos[producto][2],'Precio':DicProductos[producto][1],'Cantidad':DicProductos[producto][0]}}})
        contador.update_one({"_id":1},{"$inc":{"contador":1}})
        return render_template("recibo.html",cliente=cliente, negocio=negocio, productos=DicProductos, total=total, repartidor=repartidor)
    return redirect(request.referrer)
###################################################################################

@app.route("/logout")
def logout ():    
    return redirect("/")

@app.route("/registrar",methods=['GET'])
def registrar ():
    return render_template("RegistrarCliente.html")

@app.route("/insertar",methods=['POST']) #post para recibir 
def insertar ():
    ci=request.values.get("ci_usuario")
    ci=int(ci)
    #preguntar si el usuario ya existe
    cliente=clientes.find({"_id":ci})
    lista_cliente=list(cliente)
    if len(lista_cliente)==0:
        nombre=request.values.get("nombre_usuario")
        apellido=request.values.get("apellido_usuario")
        celular=request.values.get("celular_usuario")
        celular=int(celular)
        contra=request.values.get("contra_usuario")
        clientes.insert_one({"_id":ci,"nombreCli":nombre,"apellidoCli":apellido,"celular":celular,"contraCli":contra})
        print(mensaje_registrado_exitoso)
        return redirect("/")
    else:
        return redirect("/registrar")

@app.route("/update", methods=['POST'])
def update():
    ci=request.values.get("ci_usuario")
    ci=int(ci)
    nombre=request.values.get("nombre_usuario")
    apellido=request.values.get("apellido_usuario")
    celular=request.values.get("celular_usuario")
    celular=int(celular)
    contra=request.values.get("contra_usuario")
    print(ci,nombre,apellido,celular,contra)
    clientes.update_one({"_id":ci},{"$set":{"nombreCli":nombre,"apellidoCli":apellido,"celular":celular,"contraCli":contra}})
    #clientes.update({"_id":ci},{"$set":{"nombreCli":nombre,"apellidoCli":apellido,"celular":celular,"contraCli":contra}})
    print(mensaje_update_exitoso)
    return redirect("/datosCliente/"+format(ci))

################################# VISTA NEGOCIO ############################################
@app.route("/loginNeg", methods=['GET'])
def mostrar_login_negocio():
    return render_template("IniciarSesionNegocio.html")

LOGIN_NEG_URL = "/loginNeg" 

@app.route(LOGIN_NEG_URL, methods=['POST'])  
def login_negocio():
    nombre_neg = request.values.get("nombre_neg")
    passw = request.values.get("contra_neg")
    
    negocio = negocios.find_one({"Nombre": nombre_neg})
    if negocio:
        if negocio["Nombre"] == nombre_neg and negocio["contraNeg"] == passw:
            return redirect(f"/mostrarProdsNeg/{nombre_neg}") 
        else:
            return redirect(LOGIN_NEG_URL) 
    else:
        return redirect(LOGIN_NEG_URL) 

@app.route("/registrarNeg",methods=['GET'])
def registrar_negocio ():
    return render_template("RegistrarNegocio.html")

@app.route("/insertarNeg",methods=['POST']) #post para recibir 
def insertar_negocio ():
    nombre_neg=request.values.get("nombre_neg")
    negocio=negocios.find({"Nombre":nombre_neg})
    lista_negocio=list(negocio)
    if len(lista_negocio) == 0:
        categ=request.values.get("categoria")
        contra=request.values.get("contra_neg")
        #id tiene que ser igual autonumerico como pedido
        cont=contador.find({"_id":1})
        valor=cont[0]["contador2"]
        negocios.insert_one({"_id":valor,"Nombre":nombre_neg,"Categoria":categ,"contraNeg":contra,"Productos":[]})
        print(mensaje_registrado_exitoso)
        return redirect("/loginNeg")
    else:
        return redirect("/registrarNeg")
    
@app.route("/mostrarProdsNeg/<nombreNeg>/",methods=['GET'])
def mostrar_productos_negocio (nombre_neg):  
    negocio_p=negocios.find({"Nombre":nombre_neg})
    pipeline = [{pipeline_match:{"Nombre":nombre_neg}},{pipeline_unwind:PRODUCTOS_COLLECTION},{consulta_project:{"_id":0,"Productos":1}}]  
    productos_p=list(negocios.aggregate(pipeline))
    return render_template("ProductosNegocio.html",negocio=negocio_p,productos=productos_p)
  
def validar_estado_prod(estado):
    if estado=="Disponible":
        return "No Disponible"
    else:
        return "Disponible"

MOSTRAR_PRODS_NEG_URL = "/mostrarProdsNeg/"

@app.route("/actualizarEst/<nombreNeg>/<float:cod_prod>/<estado>/",methods=['POST'])
def actualizar_estado_prod (nombre_neg,cod_prod,estado):  
    cod_prod=float(cod_prod)
    estado=validar_estado_prod(estado)
    negocios.update_one({"Nombre":nombre_neg,"Productos.cod_prod":cod_prod},{"$set":{"Productos.$.Estado":estado}})
    return redirect(MOSTRAR_PRODS_NEG_URL +format(nombre_neg))

@app.route("/borrarProd/<nombreNeg>/<float:cod_prod>/",methods=['POST'])
def borrar_productos (nombre_neg,cod_prod):  
    cod_prod=float(cod_prod)
    negocios.update_one({"Nombre":nombre_neg},{"$pull":{"Productos":{"cod_prod":cod_prod}}})
    return redirect(MOSTRAR_PRODS_NEG_URL +format(nombre_neg))
    
@app.route("/datosNegocio/<nombreNeg>/", methods=['GET'])
def datos_negocio(nombre_neg):
    negocio_p=negocios.find({"Nombre":nombre_neg})
    return render_template("DatosNegocio.html",negocio=negocio_p)

@app.route("/actualizarNeg", methods=['POST'])
def update_negocio():
    id_neg=request.values.get("id_neg")
    id_neg=float(id_neg)
    nombre=request.values.get("nombre_neg")
    categoria=request.values.get("Categoria")
    contra=request.values.get("contra")
    negocios.update_one({"_id":id_neg},{"$set":{"Nombre":nombre,"Categoria":categoria,"contraNeg":contra}})
    #clientes.update({"_id":ci},{"$set":{"nombreCli":nombre,"apellidoCli":apellido,"celular":celular,"contraCli":contra}})
    print(mensaje_update_exitoso)
    return redirect("/datosNegocio/"+format(nombre))

@app.route("/insertarProducto/<nombreNeg>/",methods=['POST']) #post para recibir 
def insertar_producto (nombre_neg):
    cod_prod=request.values.get("id_prod")
    cod_prod=float(cod_prod)
    nombre_prod=request.values.get("NomProd")
    desc=request.values.get("descProd")
    categoria=request.values.get("CateProd")
    estado=request.values.get("Estado")
    precio=request.values.get("Precio")
    precio=int(precio)
    negocios.update_one({"Nombre":nombre_neg},{"$push":{"Productos":{"cod_prod":cod_prod,"Nombre":nombre_prod,"Precio":precio,"Descripcion":desc,"Estado":estado,"Categoria":categoria}}})
    print("Insertado con exito")
    return redirect("/mostrarProdsNeg/"+format(nombre_neg))

@app.route("/pedidosNeg/<float:idNeg>/",methods=['GET'])
def pedidos_neg (id_neg):    
    id_neg=float(id_neg)
    listapedido=list(pedidos.find({"negocioId":id_neg}))
    negocio=negocios.find({"_id":id_neg})
    return render_template("PedidosNegocio.html",pedidos=listapedido,negocio=negocio)


@app.route("/detallePedido/<float:idNeg>/<float:id_pedido>",methods=['GET'])
def detalle_pedido (id_neg,id_pedido):    
    id_pedido=float(id_pedido)
    id_neg=float(id_neg)
    pedido=list(pedidos.find({"_id":id_pedido}))
    productos=pedido[0]["productos"]
    print(pedido[0]["productos"])
    productos=list(productos)
    negocio=negocios.find({"_id":id_neg})
    return render_template("DetallePedido.html",negocio=negocio,productos=productos)
##############################################################################################

################################# VISTA REPARTIDOR ############################################
@app.route("/mostrarPedidosDisp/<id_rep>/",methods=['GET'])
def mostrar_pedidos_disp (id_rep):  
    id_rep=int(id_rep)
    repartidor=repartidores.find({"_id":id_rep})
    pedidos_rep=pedidos.find({"repartidorId":id_rep,"$or":[{"estado_ped":"pendiente"},{"estado_ped":"en camino"}]})
    return render_template("PedidosDisponibles.html",repartidor=repartidor,pedidos=pedidos_rep)

def validar_estado_rep(estado):
    if estado=="O":
        return "D"
    else:
        return "O"
    
def validar_estado_ped(estado):
    if estado=="pendiente":
        return "en camino"
    else:
        return "entregado"
    
@app.route("/actualizarEstRep/<float:id_pedido>/<id_rep>/<estado_ped>/<estado_rep>/",methods=['POST'])
def actualizar_estado_repartidor(id_pedido,id_rep,estado_ped,estado_rep):  
    id_pedido=float(id_pedido)
    id_rep=int(id_rep)
    estado_rep=validar_estado_rep(estado_rep)
    estado_ped=validar_estado_ped(estado_ped)
    repartidores.update_one({"_id":id_rep},{"$set":{"estado":estado_rep}})
    pedidos.update_one({"_id":id_pedido},{"$set":{"estado_ped":estado_ped}})
    return redirect(direccion_pedidos_disponibles+format(id_rep))

@app.route("/finalizarPedido/<float:id_pedido>/<id_rep>/<estado_ped>/<estado_rep>/",methods=['POST'])
def finalizar_pedido(id_pedido,id_rep,estado_ped,estado_rep):  
    id_pedido=float(id_pedido)
    id_rep=int(id_rep)
    estado_rep=validar_estado_rep(estado_rep)
    estado_ped=validar_estado_ped(estado_ped)
    repartidores.update_one({"_id":id_rep},{"$set":{"estado":estado_rep}})
    pedidos.update_one({"_id":id_pedido},{"$set":{"estado_ped":estado_ped}})
    return redirect(direccion_pedidos_disponibles+format(id_rep))

# Ruta para mostrar el formulario de inicio de sesión del repartidor (GET)
@app.route("/loginRep", methods=['GET'])
def mostrar_login_repartidor():
    return render_template("IniciarSesionRepartidor.html")

@app.route("/loginRep",methods=['POST']) #get para mandar 
def login_repartidor():
    _id=request.values.get("ci_rep")
    _id=int(_id)
    passw=request.values.get("contra_rep")
    repartidor=repartidores.find({"_id":_id})
    lista_repartidores=list(repartidor)
    #print(len(lista_cliente))
    if len(lista_repartidores)!= 0:
        repartidor=repartidores.find({"_id":_id})
        if(repartidor[0]["_id"]==_id and repartidor[0]["contra"]==passw):#validaciones
            #print("Id: ",cliente[0]["_id"]," pass:",cliente[0]["contraCli"])
            return redirect(direccion_pedidos_disponibles+format(_id))
        else:
            return redirect("/loginRep") #que vuelva a pedir que se registre pero con una advertencia de que el usuario o contrasenia que ingreso no existen
    else:
        return redirect("/")

@app.route("/registrarRep",methods=['GET'])
def registrar_repartidor ():
    return render_template("RegistrarRepartidor.html")

@app.route("/insertarRep",methods=['POST']) #post para recibir 
def insertar_repartidor ():
    ci=request.values.get("ci_usuario")
    ci=int(ci)
    #preguntar si el usuario ya existe
    repartidor=repartidores.find({"_id":ci})
    lista_repartidor=list(repartidor)
    if len(lista_repartidor)==0:
        nombre=request.values.get("nombre_usuario")
        apellido=request.values.get("apellido_usuario")
        celular=request.values.get("celular_usuario")
        celular=int(celular)
        contra=request.values.get("contra_usuario")
        repartidores.insert_one({"_id":ci,"Nombre":nombre,"Apellido":apellido,"celular":celular,"contra":contra,"estado":"D"})
        print(mensaje_registrado_exitoso)
        return redirect("/loginRep")
    else:
        return redirect("/registrarRep")
    
@app.route("/datosRepartidor/<id>/", methods=['GET'])
def datos_repartidor(_id):
    _id=int(_id)
    repartidor_l=repartidores.find({"_id":_id})
    print("Id: ",repartidor_l[0]["_id"]," pass:",repartidor_l[0]["contra"])
    return render_template("DatosRepartidor.html",repartidor=repartidor_l)

@app.route("/updateRep", methods=['POST'])
def update_rep():
    ci=request.values.get("ci_repartidor")
    ci=int(ci)
    nombre=request.values.get("nombre_repartidor")
    apellido=request.values.get("apellido_repartidor")
    celular=request.values.get("celular_repartidor")
    celular=int(celular)
    contra=request.values.get("contra_repartidor")
    print(ci,nombre,apellido,celular,contra)
    repartidores.update_one({"_id":ci},{"$set":{"Nombre":nombre,"Apellido":apellido,"celular":celular,"contra":contra}})
    print(mensaje_update_exitoso)
    return redirect("/datosRepartidor/"+format(ci))


@app.route("/pedidosRep/<id_rep>/",methods=['GET'])
def pedidos_rep(id_rep):
    id_rep=int(id_rep)
    listapedido=list(pedidos.find({"repartidorId":id_rep}))
    repartidor=repartidores.find({"_id":id_rep})
    return render_template("PedidosRepartidor.html",pedidos=listapedido, repartidor=repartidor)

if __name__ == "__main__":
    app.run()
