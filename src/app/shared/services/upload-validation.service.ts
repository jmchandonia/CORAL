import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';
import { Brick, TypedProperty, BrickDimension, DimensionVariable, Term, Context } from 'src/app/shared/models/brick'; 
import { UploadService } from './upload.service';

@Injectable({
  providedIn: 'root'
})
export class UploadValidationService {

  // subject that emits if errors are true
  private errorSub: Subject<any> = new Subject();
  private contextErrorSub: Subject<any> = new Subject();

  public readonly INVALID_VALUE = 'Error: invalid value for scalar type ';
  public readonly INCOMPLETE_FIELDS = 'Error: please fill out all field values before submitting.';
  public readonly INVALID_START_DATE = 'Error: Invalid brick start date';
  public readonly INVALID_END_DATE = 'Error: Invalid brick end date';
  public readonly INVALID_DATE_RANGE = 'Error: Invalid date range';

  // brick builder from upload service
  brick: Brick;

  constructor(private uploadService: UploadService) {
    // this.brick = this.uploadService.getBrickBuilder();
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
      case 'validate':
        return this.validateMappedData();
      case 'preview':
        return this.validatePreview();
      case 'create':
        return this.validateCreateStep();
      default:
        return false;
     }
   }

   getValidationErrors() {
     // components subscribe to this method to display errors if there are any
     return this.errorSub.asObservable();
   }

   getContextValidationErrors() {
     // context modals subscribe to a sepaarate subject in order to not conflict with other errors
     return this.contextErrorSub.asObservable();
   }

   validateDataType() {
    this.brick = this.uploadService.getBrickBuilder();
    if (!this.brick) {
      this.errorSub.next(true);
      return true;
    }
    this.errorSub.next(false);
    return false;
   }

   validateProperties() {
     // filter only user input properties
    let error = false;
    const messages = [];
    for (const property of this.nonRequiredProperties) {
      // check if property has type, value, and units
      if (!property.typeTerm || !property.value || property.units === undefined) {
        // this.errorSub.next(true);
        // return true;
        error = true;
        messages.push(this.INCOMPLETE_FIELDS);
      }
      if (property.value && !this.validScalarType(property.scalarType, property.value)) {
        error = true;
        property.invalidValue = true;
        messages.push(`${this.INVALID_VALUE}${property.scalarType}`);
      } else {
        property.invalidValue = false;
      }
    }
    this.errorSub.next({error, messages});
    return error;
   }

   validateDimensions() {
    for (const dimension of this.brick.dimensions) {
      for (const variable of dimension.variables) {
        // check if there is type and units for all user input dimension variables
        if ((!variable.typeTerm || variable.units === undefined) && !variable.required) {
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
        if (!dataValue.typeTerm || dataValue.units === undefined) {
          this.errorSub.next(true);
          return true;
        }
      }
      this.errorSub.next(false);
      return false;
   }

   validateUploadedData() {

    if (!this.uploadService.uploadFile || !this.uploadService.uploadSuccessData) {
      this.errorSub.next(true);
      return true;
    }
    this.errorSub.next(false);
    return false;
   }

   validateMappedData() {
     // iterate through all dimensions
     for (const dimension of this.brick.dimensions) {
       for (const variable of dimension.variables) {
         // if the mapped count does not match the total count then user needs to fix values
         if (variable.validCount !== variable.totalCount) {
           this.errorSub.next(true);
           return true;
         }
       }
     }

     // iterate through all data values
     for (const dataValue of this.brick.dataValues) {
       // if the mapped count does not match the total count then user needs to fix values
       if (dataValue.validCount !== dataValue.totalCount) {
         this.errorSub.next(true);
         return true;
       }
     }
     return false;
   }

   validateContext(context: Context[]): string[] {
     let error = false;
     const messages = [];
     for (const ctx of context) {
       if (!ctx.typeTerm || !ctx.value || ctx.units === undefined) {
         error = true;
         messages.push(this.INCOMPLETE_FIELDS);
       }
       if (ctx.value && !this.validScalarType(ctx.scalarType, ctx.value)) {
         messages.push(`${this.INVALID_VALUE}${ctx.scalarType}`);
         ctx.invalidValue = true;
         error = true;
       } else {
         ctx.invalidValue = false;
       }
     }
     this.contextErrorSub.next(error);
     return messages;
   }

   validatePreview() {
     return this.brick.coreObjectRefsError;
   }

   validateCreateStep() {
     const messages = [];
     let startDateError = false;
     let endDateError = false;
     if (
       !this.brick.name ||
       !this.brick.campaign ||
       !this.brick.personnel ||
       !this.brick.start_date ||
       !this.brick.end_date
     ) {
       messages.push(this.INCOMPLETE_FIELDS);
     }

     if (this.brick.start_date > new Date()) {
       messages.push(this.INVALID_START_DATE);
       startDateError = true;
     }

     if (this.brick.end_date > new Date()) {
       messages.push(this.INVALID_END_DATE);
       endDateError = true;
     }

     if (this.brick.start_date > this.brick.end_date) {
       messages.push(this.INVALID_DATE_RANGE);
       startDateError = endDateError = true;
     }

     return {messages, startDateError, endDateError};
   }

  public validScalarType(scalarType: string, value): boolean {
    const val = value.text ? value.text : value;
    switch (scalarType) {
      case 'int':
        return !isNaN(parseInt(val, 10)) && /^-?\d+$/.test(val);
      case 'float':
        return !isNaN(parseFloat(val)) && /^-?\d+(?:[.]\d*?)?$/.test(val);
      default:
        return true;
     }
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
