import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';
import { Brick, TypedProperty, BrickDimension, DimensionVariable, Term } from 'src/app/shared/models/brick'; 
import { UploadService } from './upload.service';

@Injectable({
  providedIn: 'root'
})
export class UploadValidationService {

  private errorSub: Subject<boolean> = new Subject();
  brick: Brick;

  constructor(private uploadService: UploadService) {
    this.brick = this.uploadService.getBrickBuilder();
   }

   validationErrors(step: string) {
     switch(step) {
      case 'properties':
        return this.validateProperties();
      case 'dimensions': 
        return this.validateDimensions();
      case 'data-values':
        return this.validateDataValues();
      case 'load':
        return this.validateUploadedData();
      default:
        return false;  
     }
   } 

   getValidationErrors() {
     return this.errorSub.asObservable();
   }

   validateProperties() {
    for (const property of this.nonRequiredProperties) {
      if (!property.type || !property.value.text || !property.units) {
        this.errorSub.next(true);
        return true;
      }
    }
    return false;
   }

   validateDimensions() {
    this.nonRequiredDimensions.forEach(dimension => {
      dimension.variables.forEach(variable => {
        if ((!variable.type || !variable.units) && !variable.required) {
          this.errorSub.next(true);
          return true;
        }
      });
    });
    return false; 
   }

   validateDataValues() {
     this.nonRequiredDataValues.forEach(dataValue => {
       if (!dataValue.type || !dataValue.units) {
         this.errorSub.next(true);
         return true;
       }
     });
     return false;
   }

   validateUploadedData() {
     this.brick.dimensions.forEach(dimension => {
       dimension.variables.forEach(variable => {
        if (!variable.valuesSample) {
          this.errorSub.next(true);
          return true;
        }
       });
     });
     return false;
   }

   get nonRequiredProperties() {
     return this.brick.properties.filter(property => !property.required);
   }

   get nonRequiredDimensions() {
     return this.brick.dimensions.filter(dimension => !dimension.required);
   }

   get nonRequiredDataValues() {
     return this.brick.dataValues.filter(dataValue => !dataValue.required);
   }


}
