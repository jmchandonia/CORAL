import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';
import { Brick, TypedProperty, BrickDimension, DimensionVariable, Term } from 'src/app/shared/models/brick'; 
import { UploadService } from './upload.service';

@Injectable({
  providedIn: 'root'
})
export class UploadValidationService {

  // subsject that emits if errors are true
  private errorSub: Subject<boolean> = new Subject();

  // brick builder from upload service
  brick: Brick;

  constructor(private uploadService: UploadService) {
    this.brick = this.uploadService.getBrickBuilder();
   }

   validationErrors(step: string) {
     // handle different brick validations depending on what step the user is on
     switch (step) {
      case 'type':
        return this.validateDataType();
      case 'properties':
        return this.validateProperties();
      case 'dimensions': 
        return this.validateDimensions();
      case 'data-variables':
        return this.validateDataVariables();
      case 'load':
        return this.validateUploadedData();
      case 'map':
        return this.validateMappedData();
      default:
        return false;
     }
   }

   getValidationErrors() {
     // components subscribe to this method to display errors if there are any
     return this.errorSub.asObservable();
   }

   validateDataType() {
     // check if brick has selected type
     if (!this.brick.type) {
       this.errorSub.next(true);
       return true;
     }
     this.errorSub.next(false);
     return false;
   }

   validateProperties() {
     // filter only user input properties
    for (const property of this.nonRequiredProperties) {
      // check if property has type, value, and units
      if (!property.type || !property.value || property.units === undefined) {
        this.errorSub.next(true);
        return true;
      }
    }
    this.errorSub.next(false);
    return false;
   }

   validateDimensions() {
    for (const dimension of this.brick.dimensions) {
      for (const variable of dimension.variables) {
        // check if there is type and units for all user input dimension variables
        if ((!variable.type || variable.units === undefined) && !variable.required) {
          this.errorSub.next(true);
          return true;
        }
      }
      // check if dimension has a type
      if (!dimension.type) {
        this.errorSub.next(true);
        return true;
      }
    }
    this.errorSub.next(false);
    return false;
   }

   validateDataVariables() {
      // filter only user input data values
      for (const dataValue of this.nonRequiredDataValues) {
        // check if data value has selected type and units
        if (!dataValue.type || !dataValue.units) {
          this.errorSub.next(true);
          return true;
        }
      }
      return false;
   }

   validateUploadedData() {
     // iterate through every dimension including template dimensions
    for (const dimension of this.brick.dimensions) {
      for (const variable of dimension.variables) {
        // if there is no values sample then the brick was not uploaded correctly or at all
        if (!variable.valuesSample) {
          this.errorSub.next(true);
          return true;
        }
      }
    }
    for (const value of this.brick.dataValues) {
      // check if datavalues each have a values sample
      if (!value.valuesSample) {
        this.errorSub.next(true);
        return true;
      }
    }
    return false;
   }

   validateMappedData() {
     // iterate through all dimensions
     for (const dimension of this.brick.dimensions) {
       for (const variable of dimension.variables) {
         // if the mapped count does not match the total count then user needs to fix values
         if (variable.mappedCount !== variable.totalCount) {
           this.errorSub.next(true);
           return true;
         }
       }
     }

     // iterate through all data values
     for (const dataValue of this.brick.dataValues) {
       // if the mapped count does not match the total count then user needs to fix values
       if (dataValue.mappedCount !== dataValue.totalCount) {
         this.errorSub.next(true);
         return true;
       }
     }
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
