areas_psmb  = '''
            DECLARE @return_value int;

            EXEC @return_value = [dbo].[Sp_Acui_no_PSMB] @usuario = 999999999

            SELECT 'Return Value' = @return_value
                    
            '''

centros_psmb = '''
            DECLARE @return_value int;

            EXEC @return_value = [dbo].[sp_acui_PSMB_Centros] @AREA = null, @usuario = 999999999;

            SELECT 'Return Value' = @return_value;
                    
            '''

existencias = '''
            DECLARE @return_value int;

            EXEC @return_value = [dbo].[sp_usach_existencia_no_salmonidos] @usuario = 999999999;

            SELECT 'Return Value' = @return_value;
                    
            '''

salmonidos = '''
             DECLARE @return_value int;

             EXEC @return_value = [dbo].[sp_usach_existencia_salmonidos] @usuario = 999999999;

             SELECT 'Return Value' = @return_value;
             '''

estaciones = '''
             DECLARE @return_value int;

             EXEC @return_value = [dbo].[sp_Acui_estaciones_areasPSMB] @AREA = null, @usuario = 999999999;

             SELECT 'Return Value' = @return_value;
             '''

detalle_caletas = '''
             DECLARE @return_value int;

             EXEC @return_value = [dbo].[sp_usach_caleta_detalle_Rpa_Emb_Org] @usuario = 999999999;

             SELECT 'Return Value' = @return_value;
             '''             