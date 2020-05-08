import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { MockComponent } from 'ng-mocks';
import { DimensionFormComponent } from './dimension-form/dimension-form.component';
import { DimensionBuilderComponent } from './dimension-builder.component';
import { HttpClientModule } from '@angular/common/http';
import { Brick } from 'src/app/shared/models/brick';
import { UploadService } from 'src/app/shared/services/upload.service';

describe('DimensionBuilderComponent', () => {

  const MockUploadService = {
    getBrickBuilder: () => new Brick()
  }

  let spectator: Spectator<DimensionBuilderComponent>;
  const createComponent = createComponentFactory({
    component: DimensionBuilderComponent,
    entryComponents: [
      MockComponent(DimensionFormComponent)
    ],
    imports: [
      HttpClientModule,
    ],
    providers: [
      mockProvider(UploadService, MockUploadService)
    ]
  });

  beforeEach(() => spectator = createComponent());


  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});
